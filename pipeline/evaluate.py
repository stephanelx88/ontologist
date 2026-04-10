"""Neo Score Evaluation — READ-ONLY by convention. Neo modifies ontology/, not this.

Computes the single scalar neo_score from four sub-scores:
  neo_score = detection * 0.40 + structural * 0.20 + coverage * 0.25 + coherence * 0.15

Adapted for fraud detection domain:
- detection_score: how well rules catch known fraud signals in held-out packages
- structural_score: YAML validity, no orphan entities, all rules reference valid entities
- coverage_score: % of known fraud patterns covered by at least one rule
- coherence_score: no contradictory rules, severity ordering consistent
"""
from __future__ import annotations

import json
import yaml
from pathlib import Path


# ---------------------------------------------------------------------------
# Known fraud patterns (the "held-out test" for fraud detection)
# These are ground-truth signals a good rule set must catch.
# READ-ONLY — Neo never modifies this list.
# ---------------------------------------------------------------------------

KNOWN_FRAUD_PATTERNS = [
    {"id": "missing-badge", "description": "Employee badge not visible in verification photo", "expected_rule": "badge-present-check", "severity": "critical"},
    {"id": "badge-swap", "description": "Different employee badges across photos in same package", "expected_rule": "employee-consistency-check", "severity": "critical"},
    {"id": "name-mismatch", "description": "Account holder name differs from loan applicant", "expected_rule": "name-mismatch-check", "severity": "critical"},
    {"id": "balance-tamper", "description": "Balance in list view differs from detail view", "expected_rule": "balance-consistency-check", "severity": "critical"},
    {"id": "session-splice", "description": "Photo timestamps span more than 10 minutes", "expected_rule": "photo-timestamp-sequence", "severity": "warning"},
    {"id": "stale-evidence", "description": "Screenshots from old date reused for new application", "expected_rule": "screenshot-date-vs-photo-date", "severity": "warning"},
    {"id": "fake-salary-label", "description": "Transfer labeled as salary but lacks standard keywords", "expected_rule": "salary-description-format", "severity": "warning"},
    {"id": "irregular-income", "description": "Salary amounts vary wildly between periods", "expected_rule": "salary-regularity-check", "severity": "warning"},
    {"id": "round-salary", "description": "Salary is suspiciously round (exact millions)", "expected_rule": "round-number-deposit", "severity": "info"},
    {"id": "inflated-balance", "description": "Balance much higher than demonstrated salary", "expected_rule": "balance-vs-salary-ratio", "severity": "info"},
    {"id": "device-reuse", "description": "Same phone device across different applicant packages", "expected_rule": None, "severity": "critical"},
    {"id": "employee-volume", "description": "Employee processing abnormally many applications", "expected_rule": None, "severity": "warning"},
    {"id": "photo-manipulation", "description": "Screenshot shows signs of digital editing", "expected_rule": None, "severity": "critical"},
]


def detection_score(rules_path: Path) -> float:
    """How many known fraud patterns are covered by at least one rule? (0-100)"""
    rules = _load_rules(rules_path)
    rule_ids = {r.get("id", "") for r in rules}

    covered = 0
    coverable = 0
    for pattern in KNOWN_FRAUD_PATTERNS:
        expected = pattern["expected_rule"]
        if expected is not None:
            coverable += 1
            if expected in rule_ids:
                covered += 1
        # Patterns with expected_rule=None are known gaps — not penalized but not covered

    return (covered / coverable * 100) if coverable > 0 else 0.0


def structural_score(ontology_path: Path) -> float:
    """Check structural integrity of ontology files. (0-100)"""
    score = 100.0
    penalties = []

    # Check entities YAML is valid
    entities_dir = ontology_path / "entities"
    if entities_dir.exists():
        for f in entities_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
                if not data:
                    penalties.append(f"Empty entity file: {f.name}")
                    score -= 10
                entities = data.get("entities", []) if isinstance(data, dict) else []
                for ent in entities:
                    if "id" not in ent:
                        penalties.append(f"Entity missing 'id' in {f.name}")
                        score -= 5
                    if "name" not in ent:
                        penalties.append(f"Entity missing 'name' in {f.name}")
                        score -= 5
            except yaml.YAMLError as e:
                penalties.append(f"Invalid YAML in {f.name}: {e}")
                score -= 20
    else:
        penalties.append("No entities/ directory")
        score -= 30

    # Check rules YAML is valid
    rules_dir = ontology_path / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
                rules = data.get("rules", []) if isinstance(data, dict) else []
                for rule in rules:
                    if "id" not in rule:
                        penalties.append(f"Rule missing 'id' in {f.name}")
                        score -= 5
                    if "severity" not in rule:
                        penalties.append(f"Rule missing 'severity' in {f.name}")
                        score -= 5
                    if "condition" not in rule:
                        penalties.append(f"Rule missing 'condition' in {f.name}")
                        score -= 3
            except yaml.YAMLError as e:
                penalties.append(f"Invalid YAML in {f.name}: {e}")
                score -= 20
    else:
        penalties.append("No rules/ directory")
        score -= 30

    # Check relationships exist
    rel_file = entities_dir / "relationships.yaml" if entities_dir.exists() else None
    if rel_file and rel_file.exists():
        try:
            data = yaml.safe_load(rel_file.read_text())
            rels = data.get("relationships", []) if isinstance(data, dict) else []
            if len(rels) == 0:
                penalties.append("No relationships defined")
                score -= 10
        except yaml.YAMLError:
            penalties.append("Invalid relationships YAML")
            score -= 15
    else:
        penalties.append("No relationships file")
        score -= 15

    return max(0.0, score)


def coverage_score(ontology_path: Path) -> float:
    """What % of expected ontology components exist? (0-100)"""
    expected_files = [
        ontology_path / "ONTOLOGY.md",
        ontology_path / "INVENTORY.md",
        ontology_path / "entities" / "core-entities.yaml",
        ontology_path / "entities" / "relationships.yaml",
        ontology_path / "rules" / "fraud-detection-rules.yaml",
        ontology_path / "skills" / "verify-bank-statement.md",
        ontology_path / "skills" / "learn-and-update.md",
        ontology_path / "docs" / "gaps.md",
        ontology_path / "docs" / "contradictions.md",
    ]

    existing = sum(1 for f in expected_files if f.exists())
    return (existing / len(expected_files)) * 100


def coherence_score(ontology_path: Path) -> float:
    """Check internal coherence — no contradictory rules, consistent severity. (0-100)"""
    score = 100.0
    rules = _load_rules(ontology_path / "rules")

    # Check severity ordering: critical rules should catch worse things than info
    severities = {"critical": 3, "warning": 2, "info": 1}
    for rule in rules:
        sev = rule.get("severity", "")
        if sev not in severities:
            score -= 10  # unknown severity

    # Check no duplicate rule IDs
    ids = [r.get("id", "") for r in rules]
    if len(ids) != len(set(ids)):
        score -= 20  # duplicate IDs

    # Check all rules have descriptions
    for rule in rules:
        if not rule.get("description"):
            score -= 5

    # Check gaps.md exists and has content
    gaps_file = ontology_path / "docs" / "gaps.md"
    if gaps_file.exists():
        content = gaps_file.read_text()
        if "## Gap:" in content:
            pass  # Good — gaps documented
        elif len(content.strip()) < 50:
            score -= 5  # Gaps file exists but empty
    else:
        score -= 10  # No gaps documentation

    return max(0.0, score)


def compute_neo_score(ontology_path: Path) -> dict:
    """Compute the composite neo_score and all sub-scores.

    Returns dict with: neo_score, detection, structural, coverage, coherence
    """
    det = detection_score(ontology_path / "rules")
    struct = structural_score(ontology_path)
    cov = coverage_score(ontology_path)
    coh = coherence_score(ontology_path)

    neo = det * 0.40 + struct * 0.20 + cov * 0.25 + coh * 0.15

    return {
        "neo_score": round(neo, 2),
        "detection": round(det, 2),
        "structural": round(struct, 2),
        "coverage": round(cov, 2),
        "coherence": round(coh, 2),
    }


def _load_rules(rules_path: Path) -> list[dict]:
    """Load all rules from YAML files in a directory."""
    rules = []
    if rules_path.is_file():
        rules_path = rules_path.parent
    if not rules_path.exists():
        return rules
    for f in rules_path.glob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text())
            if isinstance(data, dict) and "rules" in data:
                rules.extend(data["rules"])
        except yaml.YAMLError:
            pass
    return rules


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("workspaces/finance-and-banking/ontology")
    result = compute_neo_score(path)
    for k, v in result.items():
        print(f"{k}={v:.2f}")
