from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.extract import extract_package
from pipeline.graph import save_graph
from pipeline.models import FraudAssessment
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score
from pipeline.vision import ClaudeVision, GeminiVision

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VERDICT_ICONS: dict[str, str] = {
    "CLEAN": "✓",
    "REVIEW": "⚠",
    "SUSPICIOUS": "✗",
}

_SEVERITY_LABELS: dict[str, str] = {
    "CRITICAL": "CRIT",
    "WARNING": "WARN",
    "INFO": "INFO",
}

# ---------------------------------------------------------------------------
# print_summary
# ---------------------------------------------------------------------------


def print_summary(assessment: FraudAssessment) -> None:
    """Print a concise terminal summary of a fraud assessment."""
    pkg = assessment.package
    icon = _VERDICT_ICONS.get(assessment.verdict, "?")
    header = f"Neo Fraud Detection — {assessment.loan_reference}"
    separator = "━" * len(header)

    # Salary display: use first salary transaction's description if available
    salary_txns = pkg.salary_transactions
    salary_amount = salary_txns[0].amount if salary_txns else 0
    salary_desc = salary_txns[0].description or "" if salary_txns else ""

    lines: list[str] = [
        header,
        separator,
        f"Applicant:  {pkg.applicant_name or 'N/A'}",
        f"Employee:   {pkg.employee_name or 'N/A'} (ID: {pkg.employee_id or 'N/A'})",
        f"Balance:    {pkg.total_balance:,} VND",
        f"Salary:     {salary_amount:,} VND ({salary_desc})" if salary_txns else "Salary:     N/A",
        "",
        f"Risk Score: {assessment.risk_score}/100",
        f"Verdict:    {assessment.verdict} {icon}",
    ]

    if assessment.findings:
        lines.append("")
        lines.append("Findings:")
        for finding in assessment.findings:
            severity_label = finding.severity.upper()
            lines.append(f"  [{severity_label}] {finding.rule_name} — {finding.description}")

    print("\n".join(lines))


# ---------------------------------------------------------------------------
# process_single
# ---------------------------------------------------------------------------


async def process_single(
    pdf_path: Path,
    output_dir: Path,
    verbose: bool = False,
    json_only: bool = False,
) -> FraudAssessment:
    """Extract, evaluate, score, and save a single PDF loan package."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not gemini_key and not anthropic_key:
        print("Error: Set GEMINI_API_KEY or ANTHROPIC_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    if gemini_key:
        primary = GeminiVision(api_key=gemini_key)
        fallback = ClaudeVision(api_key=anthropic_key) if anthropic_key else None
        extraction_label = "gemini" if not fallback else "gemini+claude"
    else:
        primary = ClaudeVision(api_key=anthropic_key)
        fallback = None
        extraction_label = "claude"

    def on_progress(message: str) -> None:
        if verbose:
            print(f"  {message}")

    package = await extract_package(
        pdf_path=pdf_path,
        primary=primary,
        fallback=fallback,
        on_progress=on_progress,
    )

    findings = evaluate_all_rules(package)
    risk_score, verdict = compute_score(findings)

    timestamp = datetime.now(timezone.utc).isoformat()
    extraction_provider = extraction_label

    assessment = FraudAssessment(
        loan_reference=package.loan_reference,
        risk_score=risk_score,
        verdict=verdict,
        package=package,
        findings=findings,
        extraction_provider=extraction_provider,
        timestamp=timestamp,
    )

    result_dir = output_dir / package.loan_reference
    result_dir.mkdir(parents=True, exist_ok=True)

    # Always save JSON
    json_path = result_dir / "assessment.json"
    json_path.write_text(generate_json_report(assessment), encoding="utf-8")

    if not json_only:
        # Save markdown report
        md_path = result_dir / "assessment.md"
        md_path.write_text(generate_markdown_report(assessment), encoding="utf-8")

        # Save graph
        save_graph(assessment, result_dir)

    return assessment


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for the Neo fraud detection pipeline."""
    parser = argparse.ArgumentParser(
        prog="neo-fraud",
        description="Neo Fraud Detection — analyze loan application PDFs",
    )
    parser.add_argument(
        "input",
        help="PDF file path, or directory path when using --batch",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./results",
        help="Output directory (default: ./results)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all PDFs in the input directory recursively",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Skip markdown and graph output; save assessment.json only",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show per-page extraction progress",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if args.batch:
        if not input_path.is_dir():
            print(
                f"Error: '{input_path}' is not a directory (required with --batch).",
                file=sys.stderr,
            )
            sys.exit(1)

        pdf_files = sorted(input_path.rglob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in '{input_path}'.", file=sys.stderr)
            sys.exit(1)

        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file}")
            assessment = asyncio.run(
                process_single(
                    pdf_path=pdf_file,
                    output_dir=output_dir,
                    verbose=args.verbose,
                    json_only=args.json_only,
                )
            )
            print_summary(assessment)
            result_dir = output_dir / assessment.loan_reference
            print(f"\nSaved to: {result_dir}")

    else:
        if not input_path.exists():
            print(f"Error: File not found: '{input_path}'", file=sys.stderr)
            sys.exit(1)
        if not input_path.is_file():
            print(f"Error: '{input_path}' is not a file.", file=sys.stderr)
            sys.exit(1)

        assessment = asyncio.run(
            process_single(
                pdf_path=input_path,
                output_dir=output_dir,
                verbose=args.verbose,
                json_only=args.json_only,
            )
        )
        print_summary(assessment)
        result_dir = output_dir / assessment.loan_reference
        print(f"\nSaved to: {result_dir}")


if __name__ == "__main__":
    main()
