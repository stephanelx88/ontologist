"""Autoresearch iteration loop — the core learning engine.

Adapts Karpathy's autoresearch pattern for ontology refinement:
- ontology/ is the ONE modifiable workspace (like train.py)
- evaluate.py is READ-ONLY eval (like prepare.py)
- neo_score is the single scalar metric (like val_bpb)
- iterations.tsv is the experiment log (like results.tsv)
- LOOP FOREVER until plateau or user interrupts

Each iteration:
1. Read current state + past iterations
2. Identify ONE highest-impact improvement
3. Make the change to ontology/
4. Eval → neo_score
5. Keep if improved, revert if not
6. Log to iterations.tsv
7. Repeat
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.evaluate import compute_neo_score, KNOWN_FRAUD_PATTERNS


# ---------------------------------------------------------------------------
# Improvement strategies (Gap Sensing priority order from spec)
# ---------------------------------------------------------------------------

def identify_improvement(ontology_path: Path, past_iterations: list[dict]) -> dict | None:
    """Identify the single highest-impact improvement to make.

    Priority order (from spec section 9.3):
    a. Fix structural failures (free points)
    b. Fill coverage gaps (add missing rules for known patterns)
    c. Improve detection (refine existing rules)
    d. Resolve contradictions
    e. Simplify (remove elements that don't improve score)
    """
    scores = compute_neo_score(ontology_path)

    # Strategy A: Fix structural failures (cheapest points)
    if scores["structural"] < 100:
        return _find_structural_fix(ontology_path, scores)

    # Strategy B: Fill coverage gaps (add missing rules)
    if scores["coverage"] < 100:
        return _find_coverage_gap(ontology_path)

    # Strategy C: Improve detection (add rules for uncovered fraud patterns)
    if scores["detection"] < 100:
        return _find_detection_gap(ontology_path)

    # Strategy D: Simplify if everything is 100
    return _find_simplification(ontology_path, past_iterations)


def _find_structural_fix(ontology_path: Path, scores: dict) -> dict | None:
    """Find a structural issue to fix."""
    import yaml

    # Check for missing required fields in entities
    entities_dir = ontology_path / "entities"
    if entities_dir.exists():
        for f in entities_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
                if not data:
                    return {"type": "structural", "action": "fix_empty_yaml", "file": str(f), "description": f"Fix empty YAML file {f.name}"}
                entities = data.get("entities", []) if isinstance(data, dict) else []
                for ent in entities:
                    if "id" not in ent:
                        return {"type": "structural", "action": "add_entity_id", "file": str(f), "entity": ent.get("name", "unknown"), "description": f"Add missing 'id' to entity in {f.name}"}
            except yaml.YAMLError:
                return {"type": "structural", "action": "fix_yaml_syntax", "file": str(f), "description": f"Fix YAML syntax error in {f.name}"}

    # Check rules
    rules_dir = ontology_path / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
                rules = data.get("rules", []) if isinstance(data, dict) else []
                for rule in rules:
                    if "severity" not in rule:
                        return {"type": "structural", "action": "add_rule_severity", "file": str(f), "rule_id": rule.get("id", "unknown"), "description": f"Add missing 'severity' to rule {rule.get('id', 'unknown')}"}
            except yaml.YAMLError:
                return {"type": "structural", "action": "fix_yaml_syntax", "file": str(f), "description": f"Fix YAML syntax error in {f.name}"}

    return None


def _find_coverage_gap(ontology_path: Path) -> dict | None:
    """Find a missing ontology file to create."""
    expected = {
        "ONTOLOGY.md": "ontology overview",
        "INVENTORY.md": "data sources catalog",
        "entities/core-entities.yaml": "core entities",
        "entities/relationships.yaml": "entity relationships",
        "rules/fraud-detection-rules.yaml": "fraud detection rules",
        "skills/verify-bank-statement.md": "verification skill",
        "skills/learn-and-update.md": "learning feedback skill",
        "docs/gaps.md": "knowledge gaps",
        "docs/contradictions.md": "contradiction register",
    }
    for rel_path, purpose in expected.items():
        full_path = ontology_path / rel_path
        if not full_path.exists():
            return {"type": "coverage", "action": "create_file", "file": str(full_path), "purpose": purpose, "description": f"Create missing {rel_path} ({purpose})"}
    return None


def _find_detection_gap(ontology_path: Path) -> dict | None:
    """Find a known fraud pattern not covered by any rule."""
    import yaml

    # Load existing rule IDs
    rule_ids: set[str] = set()
    rules_dir = ontology_path / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text())
                for rule in data.get("rules", []):
                    rule_ids.add(rule.get("id", ""))
            except (yaml.YAMLError, AttributeError):
                pass

    # Find uncovered patterns that have expected rules
    for pattern in KNOWN_FRAUD_PATTERNS:
        expected = pattern["expected_rule"]
        if expected is not None and expected not in rule_ids:
            return {
                "type": "detection",
                "action": "add_rule",
                "pattern_id": pattern["id"],
                "expected_rule_id": expected,
                "severity": pattern["severity"],
                "description": f"Add rule '{expected}' to detect: {pattern['description']}",
            }

    # Find patterns with no expected rule (known gaps)
    for pattern in KNOWN_FRAUD_PATTERNS:
        if pattern["expected_rule"] is None:
            return {
                "type": "detection",
                "action": "design_new_rule",
                "pattern_id": pattern["id"],
                "severity": pattern["severity"],
                "description": f"Design new rule for: {pattern['description']} (currently a known gap)",
            }

    return None


def _find_simplification(ontology_path: Path, past_iterations: list[dict]) -> dict | None:
    """Look for simplification opportunities."""
    # If last 3 iterations were all "kept" with <2% improvement, suggest simplification
    if len(past_iterations) >= 3:
        recent = past_iterations[-3:]
        all_small = all(
            abs(float(it.get("neo_score", 0)) - float(past_iterations[max(0, i - 1)].get("neo_score", 0))) < 2.0
            for i, it in enumerate(recent)
        )
        if all_small:
            return {"type": "simplify", "action": "review_for_removal", "description": "Score plateau — review ontology for removable elements"}

    return None


# ---------------------------------------------------------------------------
# Iteration log I/O
# ---------------------------------------------------------------------------

def read_iterations(tsv_path: Path) -> list[dict]:
    """Read iterations.tsv into a list of dicts."""
    if not tsv_path.exists():
        return []
    rows = []
    with open(tsv_path, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def append_iteration(tsv_path: Path, iteration: dict) -> None:
    """Append one iteration row to iterations.tsv."""
    fieldnames = ["iteration", "commit", "neo_score", "detection", "structural", "coverage", "coherence", "status", "description"]
    write_header = not tsv_path.exists() or tsv_path.stat().st_size == 0

    with open(tsv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        if write_header:
            writer.writeheader()
        writer.writerow(iteration)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_commit(workspace: Path, message: str) -> str:
    """Stage ontology changes and commit. Returns commit hash."""
    subprocess.run(["git", "add", "ontology/"], cwd=workspace, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=workspace, capture_output=True)
    result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=workspace, capture_output=True, text=True)
    return result.stdout.strip()


def git_revert(workspace: Path) -> None:
    """Revert the last commit."""
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=workspace, capture_output=True)


# ---------------------------------------------------------------------------
# The Loop
# ---------------------------------------------------------------------------

def run_iteration_loop(
    workspace: Path,
    max_iterations: int = 5,
    plateau_threshold: int = 10,
    on_progress: callable | None = None,
) -> list[dict]:
    """Run the autoresearch iteration loop.

    Args:
        workspace: Path to the domain workspace (e.g., workspaces/finance-and-banking/)
        max_iterations: Maximum iterations (Phase 2 default: 5, Phase 3: unlimited)
        plateau_threshold: Consecutive reverts before stopping
        on_progress: Optional callback for status updates

    Returns:
        List of iteration result dicts
    """
    ontology_path = workspace / "ontology"
    tsv_path = workspace / "iterations.tsv"
    past = read_iterations(tsv_path)

    # Compute baseline
    baseline = compute_neo_score(ontology_path)
    if not past:
        # First run — log baseline
        commit_hash = git_commit(workspace, "neo-iter-0: baseline")
        append_iteration(tsv_path, {
            "iteration": 0,
            "commit": commit_hash,
            "neo_score": baseline["neo_score"],
            "detection": baseline["detection"],
            "structural": baseline["structural"],
            "coverage": baseline["coverage"],
            "coherence": baseline["coherence"],
            "status": "baseline",
            "description": "Initial ontology state",
        })
        past = read_iterations(tsv_path)
        if on_progress:
            on_progress(f"Baseline: neo_score={baseline['neo_score']:.2f}")

    current_score = baseline["neo_score"]
    consecutive_reverts = 0
    results = []

    for i in range(1, max_iterations + 1):
        iteration_num = len(past) + len(results)

        # Step 1: Identify improvement
        improvement = identify_improvement(ontology_path, past + results)
        if improvement is None:
            if on_progress:
                on_progress(f"Iteration {i}: No more improvements found. Score={current_score:.2f}")
            break

        if on_progress:
            on_progress(f"Iteration {i}: {improvement['description']}")

        # Step 2: The improvement itself would be applied by the caller (Neo.Architect)
        # For now, we log what SHOULD be done and eval current state
        # In production, this is where the LLM modifies ontology/ files

        # Step 3: Eval
        new_scores = compute_neo_score(ontology_path)
        new_score = new_scores["neo_score"]

        # Step 4: Decision
        improved = new_score > current_score
        simplified = (new_score == current_score)  # same score = keep if simpler

        if improved:
            status = "kept"
            commit_hash = git_commit(workspace, f"neo-iter-{iteration_num}: {improvement['description']}")
            current_score = new_score
            consecutive_reverts = 0
        elif simplified:
            status = "kept"
            commit_hash = git_commit(workspace, f"neo-iter-{iteration_num}: simplify — {improvement['description']}")
            consecutive_reverts = 0
        else:
            status = "reverted"
            git_revert(workspace)
            commit_hash = "reverted"
            consecutive_reverts += 1

        # Step 5: Log
        row = {
            "iteration": iteration_num,
            "commit": commit_hash,
            "neo_score": new_scores["neo_score"],
            "detection": new_scores["detection"],
            "structural": new_scores["structural"],
            "coverage": new_scores["coverage"],
            "coherence": new_scores["coherence"],
            "status": status,
            "description": improvement["description"],
        }
        append_iteration(tsv_path, row)
        results.append(row)

        if on_progress:
            on_progress(f"  → neo_score={new_score:.2f} ({status})")

        # Step 6: Plateau check
        if consecutive_reverts >= plateau_threshold:
            if on_progress:
                on_progress(f"Plateau: {consecutive_reverts} consecutive reverts. Stopping.")
            break

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Run iteration loop from command line."""
    import argparse
    parser = argparse.ArgumentParser(description="Neo Autoresearch Iteration Loop")
    parser.add_argument("workspace", help="Path to domain workspace")
    parser.add_argument("--max-iterations", "-n", type=int, default=5, help="Max iterations (default: 5)")
    parser.add_argument("--plateau", type=int, default=10, help="Consecutive reverts to stop (default: 10)")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    if not workspace.exists():
        print(f"Error: Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)

    def on_progress(msg: str):
        print(f"[neo] {msg}")

    print(f"Starting autoresearch loop on {workspace}")
    results = run_iteration_loop(
        workspace=workspace,
        max_iterations=args.max_iterations,
        plateau_threshold=args.plateau,
        on_progress=on_progress,
    )

    print(f"\nCompleted {len(results)} iterations")
    kept = sum(1 for r in results if r["status"] == "kept")
    reverted = sum(1 for r in results if r["status"] == "reverted")
    print(f"  Kept: {kept}, Reverted: {reverted}")

    if results:
        final = results[-1]
        print(f"  Final neo_score: {final['neo_score']}")


if __name__ == "__main__":
    main()
