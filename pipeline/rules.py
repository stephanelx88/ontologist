from __future__ import annotations

from typing import Callable

from pipeline.models import Finding, PackageData

SALARY_KEYWORDS = ["lương", "luong", "Luong", "LUONG", "salary", "Salary"]


# ---------------------------------------------------------------------------
# Rule 1: Badge present on every page
# ---------------------------------------------------------------------------

def evaluate_badge_present(pkg: PackageData) -> Finding | None:
    """Check if any page is missing a badge or has badge.visible=False."""
    missing_pages: list[int] = []

    for page in pkg.pages:
        if page.badge is None or not page.badge.visible:
            missing_pages.append(page.page_number)

    if not missing_pages:
        return None

    page_refs = ", ".join(str(p) for p in missing_pages)
    return Finding(
        rule_id="badge-present-check",
        rule_name="Badge Present Check",
        severity="critical",
        description="One or more pages are missing a visible employee badge.",
        evidence=f"Pages without visible badge: {page_refs}",
        page_reference=page_refs,
    )


# ---------------------------------------------------------------------------
# Rule 2: Employee ID consistency across pages
# ---------------------------------------------------------------------------

def evaluate_employee_consistency(pkg: PackageData) -> Finding | None:
    """Collect all badge.employee_id across pages. If >1 distinct ID, CRITICAL."""
    employee_ids: set[str] = set()

    for page in pkg.pages:
        if page.badge is not None and page.badge.employee_id is not None:
            employee_ids.add(page.badge.employee_id)

    if len(employee_ids) <= 1:
        return None

    return Finding(
        rule_id="employee-id-consistency",
        rule_name="Employee ID Consistency",
        severity="critical",
        description="Multiple distinct employee IDs found across pages.",
        evidence=f"Employee IDs found: {sorted(employee_ids)}",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 3: Holder name consistency across accounts
# ---------------------------------------------------------------------------

def evaluate_name_mismatch(pkg: PackageData) -> Finding | None:
    """Collect all holder_name from accounts. If >1 distinct name (case-insensitive), CRITICAL."""
    names: set[str] = set()

    for page in pkg.pages:
        for account in page.accounts:
            if account.holder_name is not None:
                names.add(account.holder_name.upper().strip())

    if len(names) <= 1:
        return None

    return Finding(
        rule_id="holder-name-consistency",
        rule_name="Holder Name Consistency",
        severity="critical",
        description="Multiple distinct account holder names found.",
        evidence=f"Names found: {sorted(names)}",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 4: Balance consistency — same account number, different balance
# ---------------------------------------------------------------------------

def evaluate_balance_consistency(pkg: PackageData) -> Finding | None:
    """For each account number, check if same number appears with different balances."""
    account_balances: dict[str, set[int]] = {}

    for page in pkg.pages:
        for account in page.accounts:
            buckets = account_balances.get(account.number, set())
            account_balances = {
                **account_balances,
                account.number: buckets | {account.balance},
            }

    conflicting = {
        number: balances
        for number, balances in account_balances.items()
        if len(balances) > 1
    }

    if not conflicting:
        return None

    evidence_parts = [
        f"{num}: {sorted(bals)}" for num, bals in conflicting.items()
    ]
    evidence = "; ".join(evidence_parts)

    return Finding(
        rule_id="balance-consistency",
        rule_name="Balance Consistency",
        severity="critical",
        description="Same account number appears with different balances across pages.",
        evidence=evidence,
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 5: Timestamp sequence — span > 600 seconds
# ---------------------------------------------------------------------------

def evaluate_timestamp_sequence(pkg: PackageData) -> Finding | None:
    """If photo_timestamp span across pages > 600 seconds, WARNING."""
    if pkg.session_duration_seconds is None:
        return None

    if pkg.session_duration_seconds <= 600:
        return None

    return Finding(
        rule_id="timestamp-sequence",
        rule_name="Timestamp Sequence",
        severity="warning",
        description="Photo timestamps span more than 10 minutes, suggesting session inconsistency.",
        evidence=f"Session duration: {pkg.session_duration_seconds:.0f} seconds",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 6: Screenshot freshness (not available yet)
# ---------------------------------------------------------------------------

def evaluate_screenshot_freshness(pkg: PackageData) -> Finding | None:  # noqa: ARG001
    """Return None — requires comparing photo date vs app date, not available yet."""
    return None


# ---------------------------------------------------------------------------
# Rule 7: Salary description keywords
# ---------------------------------------------------------------------------

def evaluate_salary_description(pkg: PackageData) -> Finding | None:
    """For each salary transaction, check if description contains a SALARY_KEYWORD."""
    bad_transactions: list[str] = []

    for tx in pkg.salary_transactions:
        description = tx.description or ""
        has_keyword = any(kw in description for kw in SALARY_KEYWORDS)
        if not has_keyword:
            bad_transactions.append(description or "<no description>")

    if not bad_transactions:
        return None

    return Finding(
        rule_id="salary-description-format",
        rule_name="Salary Description Format",
        severity="warning",
        description="Salary transaction(s) missing expected salary keywords in description.",
        evidence=f"Suspicious descriptions: {bad_transactions}",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 8: Salary regularity — any amount deviates >50% from average
# ---------------------------------------------------------------------------

def evaluate_salary_regularity(pkg: PackageData) -> Finding | None:
    """If 2+ salary transactions and any amount differs from average by >50%, WARNING."""
    if len(pkg.salary_transactions) < 2:
        return None

    amounts = [tx.amount for tx in pkg.salary_transactions]
    avg = sum(amounts) / len(amounts)

    outliers = [
        amount
        for amount in amounts
        if abs(amount - avg) / avg > 0.50
    ]

    if not outliers:
        return None

    return Finding(
        rule_id="salary-regularity",
        rule_name="Salary Regularity",
        severity="warning",
        description="Salary amounts are irregular — one or more transactions deviate >50% from the average.",
        evidence=f"Average: {avg:,.0f}, Outliers: {outliers}",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 9: Round numbers — salary divisible by 1_000_000
# ---------------------------------------------------------------------------

def evaluate_round_numbers(pkg: PackageData) -> Finding | None:
    """If any salary transaction amount is divisible by 1_000_000, INFO."""
    round_amounts = [
        tx.amount
        for tx in pkg.salary_transactions
        if tx.amount % 1_000_000 == 0
    ]

    if not round_amounts:
        return None

    return Finding(
        rule_id="round-number-deposit",
        rule_name="Round Number Deposit",
        severity="info",
        description="Salary transaction(s) with suspiciously round amounts (divisible by 1,000,000).",
        evidence=f"Round amounts: {round_amounts}",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Rule 10: Balance vs salary ratio — total_balance > avg_salary * 6
# ---------------------------------------------------------------------------

def evaluate_balance_salary_ratio(pkg: PackageData) -> Finding | None:
    """If total_balance > avg_salary * 6, INFO."""
    if not pkg.salary_transactions:
        return None

    amounts = [tx.amount for tx in pkg.salary_transactions]
    avg_salary = sum(amounts) / len(amounts)

    if avg_salary == 0:
        return None

    if pkg.total_balance <= avg_salary * 6:
        return None

    ratio = pkg.total_balance / avg_salary

    return Finding(
        rule_id="balance-vs-salary-ratio",
        rule_name="Balance vs Salary Ratio",
        severity="info",
        description="Total balance is more than 6× the average salary, which may indicate fabricated income.",
        evidence=f"Total balance: {pkg.total_balance:,}, Average salary: {avg_salary:,.0f}, Ratio: {ratio:.1f}×",
        page_reference=None,
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_EVALUATORS: list[Callable[[PackageData], Finding | None]] = [
    evaluate_badge_present,
    evaluate_employee_consistency,
    evaluate_name_mismatch,
    evaluate_balance_consistency,
    evaluate_timestamp_sequence,
    evaluate_screenshot_freshness,
    evaluate_salary_description,
    evaluate_salary_regularity,
    evaluate_round_numbers,
    evaluate_balance_salary_ratio,
]


def evaluate_all_rules(pkg: PackageData) -> list[Finding]:
    """Run all evaluators and return all non-None findings."""
    results: list[Finding] = []
    for evaluator in ALL_EVALUATORS:
        finding = evaluator(pkg)
        if finding is not None:
            results = [*results, finding]
    return results
