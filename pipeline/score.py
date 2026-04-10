from __future__ import annotations

from pipeline.models import Finding

_FIRST_CRITICAL = 70
_EXTRA_CRITICAL = 10
_WARNING_POINTS = 10
_INFO_POINTS = 3
_MAX_SCORE = 100


def compute_score(findings: list[Finding]) -> tuple[int, str]:
    """Compute a fraud risk score and verdict from a list of findings.

    Scoring rules:
    - First critical finding  = 70 points
    - Each additional critical = +10
    - Each warning            = +10
    - Each info               = +3
    - Capped at 100

    Verdicts:
    - 0–30  → "CLEAN"
    - 31–60 → "REVIEW"
    - 61–100 → "SUSPICIOUS"
    """
    criticals = [f for f in findings if f.severity.lower() == "critical"]
    warnings = [f for f in findings if f.severity.lower() == "warning"]
    infos = [f for f in findings if f.severity.lower() == "info"]

    score = 0

    if criticals:
        score += _FIRST_CRITICAL
        score += (len(criticals) - 1) * _EXTRA_CRITICAL

    score += len(warnings) * _WARNING_POINTS
    score += len(infos) * _INFO_POINTS

    score = min(score, _MAX_SCORE)

    if score <= 30:
        verdict = "CLEAN"
    elif score <= 60:
        verdict = "REVIEW"
    else:
        verdict = "SUSPICIOUS"

    return score, verdict
