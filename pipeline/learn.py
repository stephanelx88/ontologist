"""DREA Learning System — Do, Receive, Evaluate, Adapt.

After each fraud assessment, this module:
1. DO: Record what was done (assessment logged)
2. RECEIVE: Collect signals (findings, scores, gaps)
3. EVALUATE: Classify what went wrong or right
4. ADAPT: Propose changes to the ontology

Adaptations are written to neo/meta-knowledge/proposed/ and graduate
to ontology/rules/ after validation across multiple packages.
"""
from __future__ import annotations

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path

from pipeline.models import FraudAssessment, Finding


# ---------------------------------------------------------------------------
# Error taxonomy (from spec section 4.1)
# ---------------------------------------------------------------------------

ERROR_TYPES = {
    "extraction_miss": "Gap logged; found on re-read → re-extract",
    "hallucinated_link": "Unsourced edge flagged → remove + tighten critic",
    "wrong_abstraction": "Consumer can't map → adjust granularity",
    "causal_overclaim": "Correlation ≠ causation → downgrade to correlates",
    "stale_knowledge": "Newer source contradicts → deprecate",
    "meta_overgeneralization": "Domain B worse → narrow meta-rule scope",
}


# ---------------------------------------------------------------------------
# DREA: Do — log the action
# ---------------------------------------------------------------------------

def log_action(workspace: Path, assessment: FraudAssessment) -> Path:
    """Log a completed fraud assessment as a DREA action."""
    actions_dir = workspace / "neo" / "meta-knowledge" / "proposed" / "domain-observations"
    actions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    action_file = actions_dir / f"assessment-{assessment.loan_reference}-{timestamp}.json"
    action_file.write_text(json.dumps({
        "action_id": f"assess-{assessment.loan_reference}-{timestamp}",
        "type": "fraud_assessment",
        "timestamp": assessment.timestamp,
        "loan_reference": assessment.loan_reference,
        "risk_score": assessment.risk_score,
        "verdict": assessment.verdict,
        "findings_count": len(assessment.findings),
        "findings": [{"rule_id": f.rule_id, "severity": f.severity} for f in assessment.findings],
        "extraction_provider": assessment.extraction_provider,
        "pages_analyzed": len(assessment.package.pages),
    }, indent=2, ensure_ascii=False))

    return action_file


# ---------------------------------------------------------------------------
# DREA: Receive — collect signals from assessment
# ---------------------------------------------------------------------------

def collect_signals(assessment: FraudAssessment) -> list[dict]:
    """Extract learning signals from an assessment."""
    signals = []

    # Signal: which rules fired
    for f in assessment.findings:
        signals.append({
            "type": "rule_fired",
            "rule_id": f.rule_id,
            "severity": f.severity,
            "evidence": f.evidence,
        })

    # Signal: rules that DIDN'T fire (potential gaps)
    from pipeline.rules import ALL_EVALUATORS
    fired_ids = {f.rule_id for f in assessment.findings}
    all_rule_names = [
        "badge-present-check", "employee-consistency-check", "name-mismatch-check",
        "balance-consistency-check", "photo-timestamp-sequence", "screenshot-date-vs-photo-date",
        "salary-description-format", "salary-regularity-check", "round-number-deposit",
        "balance-vs-salary-ratio",
    ]
    for rule_id in all_rule_names:
        if rule_id not in fired_ids:
            signals.append({"type": "rule_passed", "rule_id": rule_id})

    # Signal: extraction quality
    for page in assessment.package.pages:
        if page.confidence < 0.7:
            signals.append({
                "type": "low_confidence_extraction",
                "page": page.page_number,
                "confidence": page.confidence,
                "screen_type": page.screen_type,
            })

    # Signal: novel patterns (things rules don't cover)
    pkg = assessment.package
    if pkg.salary_transactions:
        amounts = [t.amount for t in pkg.salary_transactions]
        if len(set(amounts)) == 1 and len(amounts) > 1:
            signals.append({
                "type": "novel_pattern",
                "pattern": "identical_salary_amounts",
                "description": f"All {len(amounts)} salary transactions have identical amount: {amounts[0]:,} VND",
            })

    return signals


# ---------------------------------------------------------------------------
# DREA: Evaluate — classify what happened
# ---------------------------------------------------------------------------

def evaluate_signals(signals: list[dict]) -> list[dict]:
    """Classify signals into actionable observations."""
    observations = []

    low_conf_pages = [s for s in signals if s["type"] == "low_confidence_extraction"]
    if low_conf_pages:
        observations.append({
            "error_type": "extraction_miss",
            "description": f"{len(low_conf_pages)} pages had low extraction confidence",
            "action": "Consider re-extracting with different provider or higher resolution",
            "pages": [s["page"] for s in low_conf_pages],
        })

    novel_patterns = [s for s in signals if s["type"] == "novel_pattern"]
    for pattern in novel_patterns:
        observations.append({
            "error_type": "detection_gap",
            "description": pattern["description"],
            "action": f"Propose new rule for pattern: {pattern['pattern']}",
            "pattern_id": pattern["pattern"],
        })

    return observations


# ---------------------------------------------------------------------------
# DREA: Adapt — propose changes
# ---------------------------------------------------------------------------

def propose_adaptations(
    workspace: Path,
    observations: list[dict],
    assessment: FraudAssessment,
) -> list[Path]:
    """Write proposed adaptations to neo/meta-knowledge/proposed/."""
    proposed_dir = workspace / "neo" / "meta-knowledge" / "proposed"
    proposals: list[Path] = []

    for obs in observations:
        if obs["error_type"] == "detection_gap":
            # Propose a new rule
            pattern_id = obs.get("pattern_id", "unknown")
            proposal_path = proposed_dir / "cross-domain-patterns" / f"rule-proposal-{pattern_id}.yaml"
            proposal_path.parent.mkdir(parents=True, exist_ok=True)
            proposal_path.write_text(yaml.dump({
                "proposal": {
                    "type": "new_rule",
                    "pattern_id": pattern_id,
                    "description": obs["description"],
                    "proposed_by": "neo-architect",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "evidence_from": assessment.loan_reference,
                    "status": "proposed",
                    "validated_in": [],
                    "failed_in": [],
                },
            }, allow_unicode=True))
            proposals.append(proposal_path)

    # Write gaps to ontology/docs/gaps.md
    gaps_file = workspace / "ontology" / "docs" / "gaps.md"
    if gaps_file.exists():
        existing = gaps_file.read_text()
        new_gaps = []
        for obs in observations:
            gap_title = obs["description"][:60]
            if gap_title not in existing:
                new_gaps.append(
                    f"\n## Gap: {gap_title}\n"
                    f"- **Reported by:** Neo.Architect (DREA loop)\n"
                    f"- **Source:** Assessment of {assessment.loan_reference}\n"
                    f"- **What was missing:** {obs['description']}\n"
                    f"- **Priority:** MEDIUM\n"
                    f"- **Status:** OPEN\n"
                )
        if new_gaps:
            gaps_file.write_text(existing + "\n".join(new_gaps))

    return proposals


# ---------------------------------------------------------------------------
# Full DREA cycle
# ---------------------------------------------------------------------------

def run_drea_cycle(workspace: Path, assessment: FraudAssessment) -> dict:
    """Run one full DREA cycle after an assessment.

    Returns summary of what was learned.
    """
    # DO: log
    action_file = log_action(workspace, assessment)

    # RECEIVE: collect signals
    signals = collect_signals(assessment)

    # EVALUATE: classify
    observations = evaluate_signals(signals)

    # ADAPT: propose changes
    proposals = propose_adaptations(workspace, observations, assessment)

    return {
        "action_logged": str(action_file),
        "signals_count": len(signals),
        "observations_count": len(observations),
        "proposals_count": len(proposals),
        "observations": observations,
    }
