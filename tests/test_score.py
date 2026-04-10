from __future__ import annotations

import pytest

from pipeline.models import Finding
from pipeline.score import compute_score


def _finding(severity: str, rule_id: str = "test") -> Finding:
    return Finding(
        rule_id=rule_id,
        rule_name=rule_id,
        severity=severity,
        description="test finding",
        evidence="test evidence",
        page_reference=None,
    )


def test_no_findings_returns_zero_clean() -> None:
    score, verdict = compute_score([])
    assert score == 0
    assert verdict == "CLEAN"


def test_single_critical_is_70_suspicious() -> None:
    score, verdict = compute_score([_finding("CRITICAL")])
    assert score == 70
    assert verdict == "SUSPICIOUS"


def test_two_criticals_is_80_suspicious() -> None:
    score, verdict = compute_score([_finding("CRITICAL"), _finding("CRITICAL")])
    assert score == 80
    assert verdict == "SUSPICIOUS"


def test_three_warnings_is_30_clean() -> None:
    findings = [_finding("WARNING") for _ in range(3)]
    score, verdict = compute_score(findings)
    assert score == 30
    assert verdict == "CLEAN"


def test_four_warnings_is_40_review() -> None:
    findings = [_finding("WARNING") for _ in range(4)]
    score, verdict = compute_score(findings)
    assert score == 40
    assert verdict == "REVIEW"


def test_two_infos_is_6_clean() -> None:
    findings = [_finding("INFO"), _finding("INFO")]
    score, verdict = compute_score(findings)
    assert score == 6
    assert verdict == "CLEAN"


def test_cap_at_100_with_five_criticals_five_warnings() -> None:
    findings = [_finding("CRITICAL") for _ in range(5)] + [
        _finding("WARNING") for _ in range(5)
    ]
    score, verdict = compute_score(findings)
    # Raw: 70 + 4*10 + 5*10 = 70 + 40 + 50 = 160 → capped at 100
    assert score == 100
    assert verdict == "SUSPICIOUS"


def test_mixed_one_critical_one_warning_one_info() -> None:
    findings = [_finding("CRITICAL"), _finding("WARNING"), _finding("INFO")]
    score, verdict = compute_score(findings)
    # 70 + 10 + 3 = 83
    assert score == 83
    assert verdict == "SUSPICIOUS"
