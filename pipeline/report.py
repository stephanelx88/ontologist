from __future__ import annotations

import json
from dataclasses import asdict

from pipeline.models import FraudAssessment, Finding

_SEVERITY_ICONS: dict[str, str] = {
    "CRITICAL": "🔴",
    "WARNING": "🟡",
    "INFO": "🔵",
}


def _finding_to_dict(finding: Finding) -> dict:
    return {
        "rule_id": finding.rule_id,
        "rule_name": finding.rule_name,
        "severity": finding.severity,
        "description": finding.description,
        "evidence": finding.evidence,
        "page_reference": finding.page_reference,
    }


def _salary_summary(assessment: FraudAssessment) -> dict:
    salary_txns = assessment.package.salary_transactions
    total = sum(t.amount for t in salary_txns)
    return {
        "count": len(salary_txns),
        "total_amount": total,
        "transactions": [
            {
                "amount": t.amount,
                "direction": t.direction,
                "counterparty": t.counterparty,
                "description": t.description,
                "timestamp": t.timestamp,
                "reference": t.reference,
            }
            for t in salary_txns
        ],
    }


def generate_json_report(assessment: FraudAssessment) -> str:
    """Return an indented JSON string representing the fraud assessment."""
    pkg = assessment.package

    payload = {
        "loan_reference": assessment.loan_reference,
        "risk_score": assessment.risk_score,
        "verdict": assessment.verdict,
        "extraction_provider": assessment.extraction_provider,
        "timestamp": assessment.timestamp,
        "applicant": {
            "name": pkg.applicant_name,
            "accounts": [
                {
                    "number": a.number,
                    "holder_name": a.holder_name,
                    "balance": a.balance,
                    "currency": a.currency,
                    "type": a.type,
                    "is_default": a.is_default,
                }
                for a in pkg.accounts
            ],
            "total_balance": pkg.total_balance,
        },
        "employee": {
            "name": pkg.employee_name,
            "id": pkg.employee_id,
        },
        "salary_summary": _salary_summary(assessment),
        "findings": [_finding_to_dict(f) for f in assessment.findings],
        "pages_analyzed": len(pkg.pages),
        "device": {
            "type": pkg.device_type,
            "model": pkg.device_model,
        },
    }

    return json.dumps(payload, indent=2, ensure_ascii=False)


def _verdict_line(verdict: str) -> str:
    icons = {"CLEAN": "✅", "REVIEW": "⚠️", "SUSPICIOUS": "🚨"}
    icon = icons.get(verdict, "")
    return f"{icon} **{verdict}**"


def generate_markdown_report(assessment: FraudAssessment) -> str:
    """Return a Markdown string representing the fraud assessment."""
    pkg = assessment.package
    lines: list[str] = []

    # Header
    lines.append(f"# Fraud Assessment — {assessment.loan_reference}")
    lines.append("")

    # Verdict & score
    lines.append(f"**Verdict:** {_verdict_line(assessment.verdict)}")
    lines.append(f"**Risk Score:** {assessment.risk_score} / 100")
    lines.append(f"**Timestamp:** {assessment.timestamp}")
    lines.append(f"**Provider:** {assessment.extraction_provider}")
    lines.append("")

    # Applicant info
    lines.append("## Applicant")
    lines.append(f"**Name:** {pkg.applicant_name or 'N/A'}")
    lines.append(f"**Total Balance:** {pkg.total_balance:,} VND")
    lines.append("")

    # Accounts table
    if pkg.accounts:
        lines.append("### Accounts")
        lines.append("| Account Number | Holder | Balance | Currency | Type | Default |")
        lines.append("|---|---|---|---|---|---|")
        for a in pkg.accounts:
            default = "Yes" if a.is_default else "No"
            lines.append(
                f"| {a.number} | {a.holder_name or ''} | {a.balance:,} | {a.currency} | {a.type} | {default} |"
            )
        lines.append("")

    # Employee info
    lines.append("## Employee")
    lines.append(f"**Name:** {pkg.employee_name or 'N/A'}")
    lines.append(f"**ID:** {pkg.employee_id or 'N/A'}")
    lines.append("")

    # Salary evidence
    salary_txns = pkg.salary_transactions
    lines.append("## Salary Evidence")
    if salary_txns:
        lines.append(f"**Salary transactions found:** {len(salary_txns)}")
        for t in salary_txns:
            lines.append(f"- {t.timestamp or 'N/A'}: {t.amount:,} VND — {t.description or ''} ({t.counterparty or ''})")
    else:
        lines.append("No salary transactions found.")
    lines.append("")

    # Findings
    lines.append("## Findings")
    if assessment.findings:
        for f in assessment.findings:
            icon = _SEVERITY_ICONS.get(f.severity, "⚪")
            lines.append(f"### {icon} [{f.severity}] {f.rule_name}")
            lines.append(f"**Rule ID:** `{f.rule_id}`")
            lines.append(f"**Description:** {f.description}")
            lines.append(f"**Evidence:** {f.evidence}")
            if f.page_reference:
                lines.append(f"**Page Reference:** {f.page_reference}")
            lines.append("")
    else:
        lines.append("No findings.")
        lines.append("")

    # Page count
    lines.append(f"## Pages Analyzed")
    lines.append(f"{len(pkg.pages)} page(s) processed.")

    return "\n".join(lines)
