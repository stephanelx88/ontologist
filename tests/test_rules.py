from __future__ import annotations

import pytest

from pipeline.models import (
    AccountData,
    BadgeData,
    PackageData,
    PageData,
    TransactionData,
)
from pipeline.rules import (
    ALL_EVALUATORS,
    evaluate_all_rules,
    evaluate_badge_present,
    evaluate_balance_consistency,
    evaluate_balance_salary_ratio,
    evaluate_employee_consistency,
    evaluate_name_mismatch,
    evaluate_round_numbers,
    evaluate_salary_description,
    evaluate_salary_regularity,
    evaluate_screenshot_freshness,
    evaluate_timestamp_sequence,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_badge(
    visible: bool = True,
    employee_id: str = "EMP001",
    name: str = "Doãn Thùy Hằng",
    confidence: float = 0.95,
) -> BadgeData:
    return BadgeData(
        name=name,
        employee_id=employee_id,
        visible=visible,
        confidence=confidence,
    )


def _make_account(
    number: str = "001704060001234",
    holder_name: str = "LE THI PHUONG",
    balance: int = 78_129_696,
    currency: str = "VND",
    account_type: str = "CHECKING",
    is_default: bool = True,
) -> AccountData:
    return AccountData(
        number=number,
        holder_name=holder_name,
        balance=balance,
        currency=currency,
        type=account_type,
        is_default=is_default,
    )


def _make_transaction(
    amount: int = 10_184_345,
    direction: str = "CREDIT",
    description: str = "Thanh toán lương kỳ 1",
    is_salary: bool = True,
    counterparty: str | None = "EMPLOYER CO",
    timestamp: str | None = "2024-01-31T09:00:00",
    reference: str | None = None,
) -> TransactionData:
    return TransactionData(
        amount=amount,
        direction=direction,
        counterparty=counterparty,
        description=description,
        timestamp=timestamp,
        reference=reference,
        is_salary=is_salary,
    )


def _make_page(
    page_number: int = 1,
    screen_type: str = "ACCOUNT_OVERVIEW",
    badge: BadgeData | None = None,
    accounts: list[AccountData] | None = None,
    transactions: list[TransactionData] | None = None,
    photo_timestamp: str | None = "2024-01-31T09:00:00",
) -> PageData:
    return PageData(
        page_number=page_number,
        screen_type=screen_type,
        confidence=0.95,
        badge=badge,
        accounts=accounts or [],
        transactions=transactions or [],
        device_type="SMARTPHONE",
        device_model="iPhone 14",
        photo_timestamp=photo_timestamp,
        photo_location=None,
        has_metadata=True,
        background_document_type=None,
    )


def _make_package(
    badge_visible: bool = True,
    badge_name: str = "Doãn Thùy Hằng",
    badge_employee_id: str = "EMP001",
    holder_name: str = "LE THI PHUONG",
    balance: int = 78_129_696,
    salary_amount: int = 10_184_345,
    salary_description: str = "Thanh toán lương kỳ 1",
    photo_timestamp: str = "2024-01-31T09:00:00",
) -> PackageData:
    badge = _make_badge(visible=badge_visible, name=badge_name, employee_id=badge_employee_id)
    account = _make_account(holder_name=holder_name, balance=balance)
    salary_tx = _make_transaction(
        amount=salary_amount,
        description=salary_description,
        is_salary=True,
    )
    page = _make_page(
        badge=badge,
        accounts=[account],
        transactions=[salary_tx],
        photo_timestamp=photo_timestamp,
    )
    return PackageData.from_pages("LOAN-001", [page])


# ---------------------------------------------------------------------------
# Test 1: Clean package — no CRITICAL findings
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_clean_package_no_critical_findings() -> None:
    pkg = _make_package()
    findings = evaluate_all_rules(pkg)
    critical = [f for f in findings if f.severity == "critical"]
    assert critical == [], f"Expected no critical findings but got: {critical}"


# ---------------------------------------------------------------------------
# Test 2: badge_visible=False → badge-present-check CRITICAL
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_badge_not_visible_triggers_critical() -> None:
    pkg = _make_package(badge_visible=False)
    finding = evaluate_badge_present(pkg)
    assert finding is not None
    assert finding.severity == "critical"
    assert finding.rule_id == "badge-present-check"


# ---------------------------------------------------------------------------
# Test 3: salary_amount=5_000_000 → round-number-deposit INFO
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_round_salary_amount_triggers_info() -> None:
    pkg = _make_package(salary_amount=5_000_000)
    finding = evaluate_round_numbers(pkg)
    assert finding is not None
    assert finding.severity == "info"
    assert finding.rule_id == "round-number-deposit"


# ---------------------------------------------------------------------------
# Test 4: salary_amount=10_184_345 → round-number-deposit NOT triggered
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_non_round_salary_does_not_trigger_info() -> None:
    pkg = _make_package(salary_amount=10_184_345)
    finding = evaluate_round_numbers(pkg)
    assert finding is None


# ---------------------------------------------------------------------------
# Test 5: balance=100_000_000 + salary=5_000_000 → balance-vs-salary-ratio INFO
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_high_balance_to_salary_ratio_triggers_info() -> None:
    pkg = _make_package(balance=100_000_000, salary_amount=5_000_000)
    finding = evaluate_balance_salary_ratio(pkg)
    assert finding is not None
    assert finding.severity == "info"
    assert finding.rule_id == "balance-vs-salary-ratio"


# ---------------------------------------------------------------------------
# Test 6: salary_description="TRANSFER FROM ACCOUNT" → salary-description-format WARNING
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_non_salary_description_triggers_warning() -> None:
    pkg = _make_package(salary_description="TRANSFER FROM ACCOUNT")
    finding = evaluate_salary_description(pkg)
    assert finding is not None
    assert finding.severity == "warning"
    assert finding.rule_id == "salary-description-format"


# ---------------------------------------------------------------------------
# Additional targeted tests for remaining evaluators
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_evaluate_badge_present_no_badge_on_page_triggers_critical() -> None:
    """A page with badge=None should trigger badge-present-check."""
    page = _make_page(badge=None, accounts=[_make_account()], transactions=[_make_transaction()])
    pkg = PackageData.from_pages("LOAN-002", [page])
    finding = evaluate_badge_present(pkg)
    assert finding is not None
    assert finding.severity == "critical"


@pytest.mark.unit
def test_evaluate_employee_consistency_multiple_ids_critical() -> None:
    badge1 = _make_badge(employee_id="EMP001")
    badge2 = _make_badge(employee_id="EMP002")
    page1 = _make_page(page_number=1, badge=badge1, accounts=[_make_account()])
    page2 = _make_page(page_number=2, badge=badge2, accounts=[])
    pkg = PackageData.from_pages("LOAN-003", [page1, page2])
    finding = evaluate_employee_consistency(pkg)
    assert finding is not None
    assert finding.severity == "critical"
    assert finding.rule_id == "employee-id-consistency"


@pytest.mark.unit
def test_evaluate_employee_consistency_single_id_ok() -> None:
    badge = _make_badge(employee_id="EMP001")
    page1 = _make_page(page_number=1, badge=badge, accounts=[_make_account()])
    page2 = _make_page(page_number=2, badge=badge, accounts=[])
    pkg = PackageData.from_pages("LOAN-004", [page1, page2])
    finding = evaluate_employee_consistency(pkg)
    assert finding is None


@pytest.mark.unit
def test_evaluate_name_mismatch_different_names_critical() -> None:
    acc1 = _make_account(number="ACC001", holder_name="LE THI PHUONG")
    acc2 = _make_account(number="ACC002", holder_name="NGUYEN VAN AN")
    page1 = _make_page(page_number=1, accounts=[acc1])
    page2 = _make_page(page_number=2, accounts=[acc2])
    pkg = PackageData.from_pages("LOAN-005", [page1, page2])
    finding = evaluate_name_mismatch(pkg)
    assert finding is not None
    assert finding.severity == "critical"
    assert finding.rule_id == "holder-name-consistency"


@pytest.mark.unit
def test_evaluate_balance_consistency_same_account_different_balance_critical() -> None:
    acc1 = _make_account(number="ACC001", balance=1_000_000)
    acc2 = _make_account(number="ACC001", balance=2_000_000)
    page1 = _make_page(page_number=1, accounts=[acc1])
    page2 = _make_page(page_number=2, accounts=[acc2])
    pkg = PackageData.from_pages("LOAN-006", [page1, page2])
    finding = evaluate_balance_consistency(pkg)
    assert finding is not None
    assert finding.severity == "critical"
    assert finding.rule_id == "balance-consistency"


@pytest.mark.unit
def test_evaluate_timestamp_sequence_long_span_warning() -> None:
    page1 = _make_page(page_number=1, photo_timestamp="2024-01-31T09:00:00")
    page2 = _make_page(page_number=2, photo_timestamp="2024-01-31T09:15:00")  # 15 min
    pkg = PackageData.from_pages("LOAN-007", [page1, page2])
    finding = evaluate_timestamp_sequence(pkg)
    assert finding is not None
    assert finding.severity == "warning"
    assert finding.rule_id == "timestamp-sequence"


@pytest.mark.unit
def test_evaluate_timestamp_sequence_short_span_ok() -> None:
    page1 = _make_page(page_number=1, photo_timestamp="2024-01-31T09:00:00")
    page2 = _make_page(page_number=2, photo_timestamp="2024-01-31T09:05:00")  # 5 min
    pkg = PackageData.from_pages("LOAN-008", [page1, page2])
    finding = evaluate_timestamp_sequence(pkg)
    assert finding is None


@pytest.mark.unit
def test_evaluate_screenshot_freshness_always_none() -> None:
    pkg = _make_package()
    assert evaluate_screenshot_freshness(pkg) is None


@pytest.mark.unit
def test_evaluate_salary_regularity_large_deviation_warning() -> None:
    tx1 = _make_transaction(amount=10_000_000, description="lương tháng 1")
    tx2 = _make_transaction(amount=3_000_000, description="lương tháng 2")  # <50% of avg
    page = _make_page(accounts=[_make_account()], transactions=[tx1, tx2])
    pkg = PackageData.from_pages("LOAN-009", [page])
    finding = evaluate_salary_regularity(pkg)
    assert finding is not None
    assert finding.severity == "warning"
    assert finding.rule_id == "salary-regularity"


@pytest.mark.unit
def test_evaluate_salary_regularity_consistent_ok() -> None:
    tx1 = _make_transaction(amount=10_000_000, description="lương tháng 1")
    tx2 = _make_transaction(amount=10_500_000, description="lương tháng 2")
    page = _make_page(accounts=[_make_account()], transactions=[tx1, tx2])
    pkg = PackageData.from_pages("LOAN-010", [page])
    finding = evaluate_salary_regularity(pkg)
    assert finding is None


@pytest.mark.unit
def test_all_evaluators_list_has_ten_items() -> None:
    assert len(ALL_EVALUATORS) == 10


@pytest.mark.unit
def test_evaluate_all_rules_returns_list() -> None:
    pkg = _make_package()
    results = evaluate_all_rules(pkg)
    assert isinstance(results, list)
