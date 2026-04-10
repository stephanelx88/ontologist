"""Analyze phase — pure Python, no API calls needed.

Takes pre-extracted PackageData (as JSON) and runs:
  rules → scoring → report → graph → DREA learning

This is the phase that runs after vision extraction. In Claude Code mode,
Claude reads the PDF pages with native vision and produces the JSON.
In API mode, vision.py produces it. Either way, this module takes over.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.models import (
    AccountData, BadgeData, FraudAssessment, PackageData, PageData, TransactionData,
)
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.graph import save_graph


def package_from_json(data: dict) -> PackageData:
    """Build a PackageData from a JSON dict (extracted by vision or Claude Code)."""
    pages = []
    for p in data.get("pages", []):
        badge_raw = p.get("badge")
        badge = None
        if badge_raw and badge_raw.get("visible"):
            badge = BadgeData(
                name=badge_raw.get("name"),
                employee_id=str(badge_raw.get("employee_id")) if badge_raw.get("employee_id") else None,
                visible=badge_raw.get("visible", False),
                confidence=badge_raw.get("confidence", 0.0),
            )

        accounts = [
            AccountData(
                number=str(a.get("number", "")),
                holder_name=a.get("holder_name"),
                balance=int(a.get("balance", 0)),
                currency=a.get("currency", "VND"),
                type=a.get("type", "payment"),
                is_default=a.get("is_default", False),
            )
            for a in p.get("accounts", [])
        ]

        transactions = [
            TransactionData(
                amount=int(t.get("amount", 0)),
                direction=t.get("direction", "incoming"),
                counterparty=t.get("counterparty"),
                description=t.get("description"),
                timestamp=t.get("timestamp"),
                reference=t.get("reference"),
                is_salary=t.get("is_salary", False),
            )
            for t in p.get("transactions", [])
        ]

        pages.append(PageData(
            page_number=p.get("page_number", 0),
            screen_type=p.get("screen_type", "unknown"),
            confidence=p.get("confidence", 0.9),
            badge=badge,
            accounts=accounts,
            transactions=transactions,
            device_type=p.get("device", {}).get("type") if isinstance(p.get("device"), dict) else p.get("device_type"),
            device_model=p.get("device", {}).get("model") if isinstance(p.get("device"), dict) else p.get("device_model"),
            photo_timestamp=p.get("photo_metadata", {}).get("timestamp") if isinstance(p.get("photo_metadata"), dict) else p.get("photo_timestamp"),
            photo_location=p.get("photo_metadata", {}).get("location") if isinstance(p.get("photo_metadata"), dict) else p.get("photo_location"),
            has_metadata=p.get("photo_metadata", {}).get("has_metadata", False) if isinstance(p.get("photo_metadata"), dict) else p.get("has_metadata", False),
            background_document_type=p.get("background_document", {}).get("type") if isinstance(p.get("background_document"), dict) else p.get("background_document_type"),
        ))

    loan_ref = data.get("loan_reference", "UNKNOWN")
    return PackageData.from_pages(loan_reference=loan_ref, pages=pages)


def analyze_package(
    package_data: dict,
    output_dir: Path | None = None,
) -> FraudAssessment:
    """Run the full analysis pipeline on pre-extracted package data.

    Args:
        package_data: Dict with 'loan_reference' and 'pages' (from vision extraction)
        output_dir: Where to save reports. If None, uses ./results/{loan_ref}/

    Returns:
        FraudAssessment with score, verdict, findings
    """
    pkg = package_from_json(package_data)
    findings = evaluate_all_rules(pkg)
    risk_score, verdict = compute_score(findings)

    assessment = FraudAssessment(
        loan_reference=pkg.loan_reference,
        risk_score=risk_score,
        verdict=verdict,
        package=pkg,
        findings=findings,
        extraction_provider="claude-code",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Save outputs
    if output_dir is None:
        output_dir = Path("./results") / pkg.loan_reference
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "assessment.json").write_text(
        generate_json_report(assessment), encoding="utf-8"
    )
    (output_dir / "assessment.md").write_text(
        generate_markdown_report(assessment), encoding="utf-8"
    )
    save_graph(assessment, output_dir)

    # DREA learning
    workspace = _find_workspace()
    if workspace:
        from pipeline.learn import run_drea_cycle
        run_drea_cycle(workspace, assessment)

    return assessment


def _find_workspace() -> Path | None:
    """Find the nearest workspace directory."""
    candidates = [
        Path("workspaces/finance-and-banking"),
        Path.cwd() / "workspaces" / "finance-and-banking",
    ]
    for c in candidates:
        if c.exists() and (c / "ontology").exists():
            return c
    return None


def main():
    """CLI: analyze a pre-extracted JSON file."""
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.analyze <extracted.json> [output_dir]")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    data = json.loads(json_path.read_text())
    assessment = analyze_package(data, output_dir)

    # Print summary
    pkg = assessment.package
    print(f"\nNeo Fraud Detection — {assessment.loan_reference}")
    print("━" * 40)
    print(f"Applicant:  {pkg.applicant_name or 'Unknown'}")
    print(f"Employee:   {pkg.employee_name or 'Unknown'} (ID: {pkg.employee_id or '?'})")
    print(f"Balance:    {pkg.total_balance:,} VND")
    print(f"Risk Score: {assessment.risk_score}/100")
    print(f"Verdict:    {assessment.verdict}")
    if assessment.findings:
        print("\nFindings:")
        for f in assessment.findings:
            print(f"  [{f.severity.upper()}] {f.rule_name} — {f.description}")


if __name__ == "__main__":
    main()
