from __future__ import annotations

import json

import pytest

from pipeline.models import Finding, FraudAssessment, PackageData
from pipeline.report import generate_json_report, generate_markdown_report


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        rule_id="RULE_001",
        rule_name="Suspicious Balance",
        severity="CRITICAL",
        description="Account balance inconsistent with stated income.",
        evidence="Balance 78,129,696 VND on single statement.",
        page_reference="page_1",
    )


@pytest.fixture
def sample_assessment(
    sample_package_data: PackageData,
    sample_finding: Finding,
) -> FraudAssessment:
    return FraudAssessment(
        loan_reference="LOAN-2024-00123",
        risk_score=70,
        verdict="SUSPICIOUS",
        package=sample_package_data,
        findings=[sample_finding],
        extraction_provider="gemini-2.5-pro",
        timestamp="2024-04-01T12:00:00",
    )


# --- JSON report tests ---


def test_json_report_is_valid_json(sample_assessment: FraudAssessment) -> None:
    result = generate_json_report(sample_assessment)
    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_json_report_has_correct_loan_reference(sample_assessment: FraudAssessment) -> None:
    result = generate_json_report(sample_assessment)
    parsed = json.loads(result)
    assert parsed["loan_reference"] == "LOAN-2024-00123"


def test_json_report_has_correct_verdict(sample_assessment: FraudAssessment) -> None:
    result = generate_json_report(sample_assessment)
    parsed = json.loads(result)
    assert parsed["verdict"] == "SUSPICIOUS"


def test_json_report_has_correct_risk_score(sample_assessment: FraudAssessment) -> None:
    result = generate_json_report(sample_assessment)
    parsed = json.loads(result)
    assert parsed["risk_score"] == 70


def test_json_report_includes_findings_array(sample_assessment: FraudAssessment) -> None:
    result = generate_json_report(sample_assessment)
    parsed = json.loads(result)
    assert "findings" in parsed
    assert isinstance(parsed["findings"], list)
    assert len(parsed["findings"]) == 1
    assert parsed["findings"][0]["rule_id"] == "RULE_001"


# --- Markdown report tests ---


def test_markdown_has_fraud_assessment_header(sample_assessment: FraudAssessment) -> None:
    result = generate_markdown_report(sample_assessment)
    assert "# Fraud Assessment" in result


def test_markdown_contains_loan_reference(sample_assessment: FraudAssessment) -> None:
    result = generate_markdown_report(sample_assessment)
    assert "LOAN-2024-00123" in result


def test_markdown_contains_verdict(sample_assessment: FraudAssessment) -> None:
    result = generate_markdown_report(sample_assessment)
    assert "SUSPICIOUS" in result


def test_markdown_contains_applicant_name(sample_assessment: FraudAssessment) -> None:
    result = generate_markdown_report(sample_assessment)
    # The applicant name comes from the account holder in conftest
    assert "LE THI PHUONG" in result
