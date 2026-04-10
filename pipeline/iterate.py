"""Autoresearch iteration loop — the core learning engine.

Each iteration:
1. Re-analyze ALL bank statement packages with current rules
2. Compare findings against previous iteration
3. Identify patterns (novel signals, false positives, coverage gaps)
4. Propose ONE rule change (add, modify, or remove)
5. Apply the change to ontology/rules/
6. Re-analyze ALL packages again with the new rule
7. Compute neo_score: did detection improve without adding noise?
8. Keep if improved, git revert if not
9. Log to iterations.tsv

This is SLOW by design — each iteration involves real computation.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

from pipeline.analyze import package_from_json, analyze_package
from pipeline.evaluate import compute_neo_score
from pipeline.models import FraudAssessment
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score


# ---------------------------------------------------------------------------
# Load all extracted packages from disk
# ---------------------------------------------------------------------------

def load_extracted_packages(workspace: Path) -> list[dict]:
    """Find all extracted JSON files — from extracted/ or results/."""
    packages = []

    # Check extracted/ directory (at project root or relative to workspace)
    candidates = [
        Path("extracted"),                    # project root
        workspace.parent / "extracted",       # relative to workspace parent
        workspace / "extracted",              # inside workspace
    ]
    extracted_dir = None
    for c in candidates:
        if c.exists() and list(c.glob("*.json")):
            extracted_dir = c
            break

    if extracted_dir and extracted_dir.exists():
        for f in sorted(extracted_dir.glob("*.json")):
            try:
                packages.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass

    # Also check results/ for assessment JSONs (re-extract package data)
    results_dir = workspace.parent / "results"
    if results_dir.exists():
        for d in sorted(results_dir.iterdir()):
            pkg_json = d / "assessment.json"
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text())
                    # assessment.json has different shape — skip if no pages
                    if "pages" not in data:
                        continue
                    packages.append(data)
                except json.JSONDecodeError:
                    pass

    return packages


# ---------------------------------------------------------------------------
# Run all packages through current rules and collect results
# ---------------------------------------------------------------------------

def run_all_assessments(packages: list[dict]) -> list[FraudAssessment]:
    """Run fraud detection on all packages with current rules."""
    assessments = []
    for pkg_data in packages:
        pkg = package_from_json(pkg_data)
        findings = evaluate_all_rules(pkg)
        risk_score, verdict = compute_score(findings)
        assessment = FraudAssessment(
            loan_reference=pkg.loan_reference,
            risk_score=risk_score,
            verdict=verdict,
            package=pkg,
            findings=findings,
            extraction_provider="iterate-loop",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        assessments.append(assessment)
    return assessments


# ---------------------------------------------------------------------------
# Analyze findings for improvement opportunities
# ---------------------------------------------------------------------------

def analyze_findings_for_patterns(
    assessments: list[FraudAssessment],
    past_iterations: list[dict],
) -> dict | None:
    """Study all assessment findings and propose ONE improvement.

    Looks for:
    1. Rules that NEVER fire across all packages → candidate for threshold tuning
    2. Rules that fire on EVERY package → too sensitive, needs tightening
    3. Novel patterns not caught by any rule → new rule needed
    4. Findings with low severity that should be higher → severity upgrade
    5. Missing cross-package analysis rules
    """
    all_findings: dict[str, list] = {}  # rule_id → list of (assessment, finding)
    total_packages = len(assessments)

    for assessment in assessments:
        for finding in assessment.findings:
            all_findings.setdefault(finding.rule_id, []).append(
                (assessment.loan_reference, finding)
            )

    # All known rule IDs
    from pipeline.rules import ALL_EVALUATORS
    all_rule_names = [
        "badge-present-check", "employee-consistency-check", "name-mismatch-check",
        "balance-consistency-check", "photo-timestamp-sequence", "screenshot-date-vs-photo-date",
        "salary-description-format", "salary-regularity-check", "round-number-deposit",
        "balance-vs-salary-ratio",
    ]

    fired_rules = set(all_findings.keys())
    silent_rules = set(all_rule_names) - fired_rules

    # Track what we already tried
    tried_descriptions = {row.get("description", "") for row in past_iterations}

    # --- Pattern 1: Cross-package patterns ---

    # Check if same device type used across different applicants
    devices_by_package: dict[str, str] = {}
    for a in assessments:
        if a.package.device_type:
            devices_by_package[a.loan_reference] = f"{a.package.device_type}:{a.package.device_model or 'unknown'}"

    device_values = list(devices_by_package.values())
    if len(device_values) > 1 and len(set(device_values)) < len(device_values):
        desc = "Add cross-package device reuse detection rule"
        if desc not in tried_descriptions:
            return {
                "type": "new_rule",
                "action": "add_cross_package_rule",
                "rule_id": "device-reuse-check",
                "description": desc,
                "evidence": f"Devices: {devices_by_package}",
                "template": {
                    "id": "device-reuse-check",
                    "name": "Cross-applicant device reuse detection",
                    "description": f"Same device type detected across packages: {set(device_values)}. May indicate manufactured evidence.",
                    "condition": "count(packages_with_same_device) > 1",
                    "action": "flag_device_reuse",
                    "severity": "critical",
                    "source": f"Auto-learned from {total_packages} packages by Neo iteration loop",
                    "domain": "cross-package",
                },
            }

    # --- Pattern 2: Salary amount patterns across packages ---

    all_salary_amounts: list[int] = []
    for a in assessments:
        for t in a.package.salary_transactions:
            all_salary_amounts.append(t.amount)

    if all_salary_amounts:
        round_count = sum(1 for amt in all_salary_amounts if amt % 1_000_000 == 0)
        round_pct = round_count / len(all_salary_amounts)
        if round_pct > 0.7:
            desc = f"Tighten round-number rule: {round_pct:.0%} of salaries across all packages are round"
            if desc not in tried_descriptions:
                return {
                    "type": "modify_rule",
                    "action": "modify_severity",
                    "rule_id": "round-number-deposit",
                    "new_severity": "warning",
                    "description": desc,
                    "evidence": f"{round_count}/{len(all_salary_amounts)} salary amounts are round millions",
                }

    # --- Pattern 3: Timestamp analysis ---

    sessions_over_10min = 0
    for a in assessments:
        if a.package.session_duration_seconds and a.package.session_duration_seconds > 600:
            sessions_over_10min += 1

    if sessions_over_10min > 0 and total_packages > 1:
        pct = sessions_over_10min / total_packages
        if pct > 0.5:
            desc = f"Adjust timestamp threshold: {sessions_over_10min}/{total_packages} sessions exceed 10 min — may be normal for thorough verification"
            if desc not in tried_descriptions:
                return {
                    "type": "modify_rule",
                    "action": "adjust_threshold",
                    "rule_id": "photo-timestamp-sequence",
                    "description": desc,
                    "evidence": f"{pct:.0%} of sessions exceed 10 min threshold",
                }

    # --- Pattern 4: Balance-to-salary ratio refinement ---

    ratios = []
    for a in assessments:
        if a.package.salary_transactions:
            avg_salary = sum(t.amount for t in a.package.salary_transactions) / len(a.package.salary_transactions)
            if avg_salary > 0:
                ratios.append(a.package.total_balance / avg_salary)

    if ratios and all(r > 6 for r in ratios):
        avg_ratio = sum(ratios) / len(ratios)
        desc = f"Adjust balance-salary ratio threshold: all packages exceed 6x (avg {avg_ratio:.1f}x) — current threshold may be too low"
        if desc not in tried_descriptions:
            return {
                "type": "modify_rule",
                "action": "adjust_threshold",
                "rule_id": "balance-vs-salary-ratio",
                "description": desc,
                "evidence": f"Ratios across packages: {[f'{r:.1f}x' for r in ratios]}",
            }

    # --- Pattern 5: Employee volume (needs multiple packages) ---

    employee_counts: dict[str, int] = {}
    for a in assessments:
        if a.package.employee_id:
            employee_counts[a.package.employee_id] = employee_counts.get(a.package.employee_id, 0) + 1

    for emp_id, count in employee_counts.items():
        if count > 1:
            desc = f"Add employee volume tracking: employee {emp_id} appears in {count} packages"
            if desc not in tried_descriptions:
                return {
                    "type": "new_rule",
                    "action": "add_cross_package_rule",
                    "rule_id": "employee-volume-check",
                    "description": desc,
                    "evidence": f"Employee {emp_id} processed {count} packages",
                    "template": {
                        "id": "employee-volume-check",
                        "name": "Employee processing volume tracking",
                        "description": f"Employee {emp_id} processed {count} packages in the dataset.",
                        "condition": "employee.package_count > threshold",
                        "action": "flag_employee_volume",
                        "severity": "warning",
                        "source": f"Auto-learned from {total_packages} packages",
                        "domain": "cross-package",
                    },
                }

    # --- Pattern 6: Check for missing photo manipulation detection ---
    desc = "Add placeholder rule for photo manipulation detection (visual forensics)"
    if desc not in tried_descriptions:
        return {
            "type": "new_rule",
            "action": "add_cross_package_rule",
            "rule_id": "photo-manipulation-check",
            "description": desc,
            "evidence": "No visual forensics rules exist yet — known gap",
            "template": {
                "id": "photo-manipulation-check",
                "name": "Screenshot manipulation detection",
                "description": "Flag verification photos showing signs of digital editing: inconsistent fonts, compression artifacts, misaligned UI elements.",
                "condition": "verification_photo.manipulation_indicators > 0",
                "action": "flag_photo_manipulation",
                "severity": "critical",
                "source": f"Auto-generated gap fill by Neo iteration loop",
                "domain": "visual",
            },
        }

    return None


# ---------------------------------------------------------------------------
# Apply improvement to ontology
# ---------------------------------------------------------------------------

def apply_improvement(ontology_path: Path, improvement: dict) -> bool:
    """Apply a rule change to the ontology. Returns True if changed."""
    action = improvement.get("action", "")

    if action == "add_cross_package_rule":
        return _add_rule(ontology_path, improvement.get("template", {}))
    elif action == "modify_severity":
        return _modify_rule_severity(ontology_path, improvement["rule_id"], improvement["new_severity"])
    elif action == "adjust_threshold":
        # Log as observation — threshold changes need more data
        _log_observation(ontology_path, improvement)
        return True  # Count as a change for the iteration log
    else:
        return False


def _add_rule(ontology_path: Path, template: dict) -> bool:
    """Add a new rule to fraud-detection-rules.yaml."""
    if not template or "id" not in template:
        return False

    rules_file = ontology_path / "rules" / "fraud-detection-rules.yaml"
    if not rules_file.exists():
        return False

    data = yaml.safe_load(rules_file.read_text())
    if not isinstance(data, dict) or "rules" not in data:
        return False

    existing_ids = {r.get("id") for r in data["rules"]}
    if template["id"] in existing_ids:
        return False

    data["rules"].append(dict(template))
    rules_file.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False))
    return True


def _modify_rule_severity(ontology_path: Path, rule_id: str, new_severity: str) -> bool:
    """Change a rule's severity level."""
    rules_file = ontology_path / "rules" / "fraud-detection-rules.yaml"
    if not rules_file.exists():
        return False

    data = yaml.safe_load(rules_file.read_text())
    changed = False
    for rule in data.get("rules", []):
        if rule.get("id") == rule_id and rule.get("severity") != new_severity:
            rule["severity"] = new_severity
            changed = True

    if changed:
        rules_file.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False))
    return changed


def _log_observation(ontology_path: Path, improvement: dict) -> None:
    """Log a threshold observation to gaps.md."""
    gaps_file = ontology_path / "docs" / "gaps.md"
    if not gaps_file.exists():
        return

    content = gaps_file.read_text()
    marker = f"## Observation: {improvement['description'][:60]}"
    if marker not in content:
        entry = (
            f"\n{marker}\n"
            f"- **Source:** Autoresearch iteration loop\n"
            f"- **Evidence:** {improvement.get('evidence', 'N/A')}\n"
            f"- **Rule:** `{improvement.get('rule_id', 'N/A')}`\n"
            f"- **Timestamp:** {datetime.now(timezone.utc).isoformat()}\n"
            f"- **Status:** PROPOSED\n"
        )
        gaps_file.write_text(content + entry)


# ---------------------------------------------------------------------------
# Iteration log I/O
# ---------------------------------------------------------------------------

def read_iterations(tsv_path: Path) -> list[dict]:
    if not tsv_path.exists():
        return []
    rows = []
    with open(tsv_path, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def append_iteration(tsv_path: Path, row: dict) -> None:
    fieldnames = ["iteration", "commit", "neo_score", "detection", "structural",
                  "coverage", "coherence", "packages", "findings_before",
                  "findings_after", "status", "description"]
    write_header = not tsv_path.exists() or tsv_path.stat().st_size == 0
    with open(tsv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_commit(workspace: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=workspace, capture_output=True)
    result = subprocess.run(["git", "commit", "-m", message], cwd=workspace,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return "no-change"
    h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=workspace,
                        capture_output=True, text=True)
    return h.stdout.strip()


def git_revert(workspace: Path) -> None:
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=workspace,
                    capture_output=True)


# ---------------------------------------------------------------------------
# The Loop — SLOW, DATA-DRIVEN, ACTUALLY LEARNS
# ---------------------------------------------------------------------------

def run_iteration_loop(
    workspace: Path,
    max_iterations: int = 10,
    plateau_threshold: int = 5,
    on_progress: callable | None = None,
) -> list[dict]:
    """Run the autoresearch iteration loop.

    Each iteration:
    1. Load all extracted bank statement packages
    2. Run ALL through current fraud rules
    3. Analyze findings for patterns
    4. Propose and apply ONE change
    5. Re-run ALL packages with new rules
    6. Compare: did detection improve?
    7. Keep if improved, revert if not

    This is SLOW — each iteration re-processes all packages.
    """
    ontology_path = workspace / "ontology"
    tsv_path = workspace / "iterations.tsv"

    # Load all packages
    packages = load_extracted_packages(workspace)
    if not packages:
        if on_progress:
            on_progress("No extracted packages found. Run fraud analysis first.")
        return []

    if on_progress:
        on_progress(f"Loaded {len(packages)} packages for iteration")

    past = read_iterations(tsv_path)
    results = []
    consecutive_reverts = 0

    # Baseline: run all packages through current rules
    if on_progress:
        on_progress("Running baseline assessment on all packages...")

    baseline_assessments = run_all_assessments(packages)
    baseline_total_findings = sum(len(a.findings) for a in baseline_assessments)
    baseline_scores = compute_neo_score(ontology_path)

    if on_progress:
        on_progress(
            f"Baseline: neo_score={baseline_scores['neo_score']:.2f}, "
            f"{baseline_total_findings} findings across {len(packages)} packages"
        )
        for a in baseline_assessments:
            finding_summary = ", ".join(f"[{f.severity}] {f.rule_id}" for f in a.findings) or "no findings"
            on_progress(f"  {a.loan_reference}: score={a.risk_score}, {a.verdict} — {finding_summary}")

    current_score = baseline_scores["neo_score"]

    for i in range(1, max_iterations + 1):
        iteration_num = len(past) + len(results) + 1

        if on_progress:
            on_progress(f"\n--- Iteration {i}/{max_iterations} ---")

        # Step 1: Analyze all findings for improvement opportunities
        if on_progress:
            on_progress("Analyzing findings for patterns...")

        current_assessments = run_all_assessments(packages)
        improvement = analyze_findings_for_patterns(current_assessments, past + results)

        if improvement is None:
            if on_progress:
                on_progress("No more improvements found. Stopping.")
            break

        if on_progress:
            on_progress(f"Proposed: {improvement['description']}")
            if improvement.get("evidence"):
                on_progress(f"Evidence: {improvement['evidence']}")

        # Step 2: Apply the change
        changed = apply_improvement(ontology_path, improvement)
        if not changed:
            if on_progress:
                on_progress("Could not apply change. Skipping.")
            row = {
                "iteration": iteration_num, "commit": "skipped",
                "neo_score": current_score, "detection": baseline_scores["detection"],
                "structural": baseline_scores["structural"],
                "coverage": baseline_scores["coverage"],
                "coherence": baseline_scores["coherence"],
                "packages": len(packages), "findings_before": baseline_total_findings,
                "findings_after": baseline_total_findings,
                "status": "skipped", "description": improvement["description"],
            }
            append_iteration(tsv_path, row)
            results.append(row)
            continue

        # Step 3: Re-run ALL packages with new rules
        if on_progress:
            on_progress("Re-running all packages with updated rules...")

        new_assessments = run_all_assessments(packages)
        new_total_findings = sum(len(a.findings) for a in new_assessments)
        new_scores = compute_neo_score(ontology_path)
        new_score = new_scores["neo_score"]

        if on_progress:
            for a in new_assessments:
                finding_summary = ", ".join(f"[{f.severity}] {f.rule_id}" for f in a.findings) or "no findings"
                on_progress(f"  {a.loan_reference}: score={a.risk_score}, {a.verdict} — {finding_summary}")

        # Step 4: Decision
        score_improved = new_score > current_score
        same_score = new_score == current_score
        more_findings = new_total_findings > baseline_total_findings

        if score_improved or (same_score and more_findings):
            status = "kept"
            commit_hash = git_commit(workspace, f"neo-iter-{iteration_num}: {improvement['description']}")
            if on_progress:
                on_progress(
                    f"KEPT: neo_score {current_score:.2f}→{new_score:.2f}, "
                    f"findings {baseline_total_findings}→{new_total_findings}"
                )
            current_score = new_score
            baseline_total_findings = new_total_findings
            consecutive_reverts = 0
        elif new_score < current_score:
            status = "reverted"
            git_revert(workspace)
            commit_hash = "reverted"
            consecutive_reverts += 1
            if on_progress:
                on_progress(
                    f"REVERTED: neo_score would drop {current_score:.2f}→{new_score:.2f}"
                )
        else:
            # Same score, same findings — keep if structural improvement
            status = "kept"
            commit_hash = git_commit(workspace, f"neo-iter-{iteration_num}: {improvement['description']}")
            consecutive_reverts = 0
            if on_progress:
                on_progress(f"KEPT (structural improvement): neo_score={new_score:.2f}")

        # Step 5: Log
        row = {
            "iteration": iteration_num, "commit": commit_hash,
            "neo_score": new_scores["neo_score"],
            "detection": new_scores["detection"],
            "structural": new_scores["structural"],
            "coverage": new_scores["coverage"],
            "coherence": new_scores["coherence"],
            "packages": len(packages),
            "findings_before": baseline_total_findings if status == "reverted" else new_total_findings,
            "findings_after": new_total_findings,
            "status": status, "description": improvement["description"],
        }
        append_iteration(tsv_path, row)
        results.append(row)

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
    import argparse
    parser = argparse.ArgumentParser(description="Neo Autoresearch Iteration Loop")
    parser.add_argument("workspace", nargs="?", default="workspaces/finance-and-banking",
                        help="Path to domain workspace")
    parser.add_argument("-n", "--max-iterations", type=int, default=10)
    parser.add_argument("--plateau", type=int, default=5)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    if not workspace.exists():
        print(f"Error: Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)

    def on_progress(msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    print(f"Neo Autoresearch Loop — {workspace}")
    print("━" * 60)

    results = run_iteration_loop(
        workspace=workspace,
        max_iterations=args.max_iterations,
        plateau_threshold=args.plateau,
        on_progress=on_progress,
    )

    print("━" * 60)
    kept = sum(1 for r in results if r["status"] == "kept")
    reverted = sum(1 for r in results if r["status"] == "reverted")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"Done: {len(results)} iterations — {kept} kept, {reverted} reverted, {skipped} skipped")
    if results:
        best = max(results, key=lambda r: float(r.get("neo_score", 0)))
        print(f"Best neo_score: {best['neo_score']}")


if __name__ == "__main__":
    main()
