from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BadgeData:
    name: Optional[str]
    employee_id: Optional[str]
    visible: bool
    confidence: float


@dataclass(frozen=True)
class AccountData:
    number: str
    holder_name: Optional[str]
    balance: int
    currency: str
    type: str
    is_default: bool


@dataclass(frozen=True)
class TransactionData:
    amount: int
    direction: str
    counterparty: Optional[str]
    description: Optional[str]
    timestamp: Optional[str]
    reference: Optional[str]
    is_salary: bool


@dataclass(frozen=True)
class PageData:
    page_number: int
    screen_type: str
    confidence: float
    badge: Optional[BadgeData]
    accounts: list[AccountData]
    transactions: list[TransactionData]
    device_type: Optional[str]
    device_model: Optional[str]
    photo_timestamp: Optional[str]
    photo_location: Optional[str]
    has_metadata: bool
    background_document_type: Optional[str]


@dataclass(frozen=True)
class PackageData:
    loan_reference: str
    pages: list[PageData]
    applicant_name: Optional[str]
    employee_name: Optional[str]
    employee_id: Optional[str]
    accounts: list[AccountData]
    transactions: list[TransactionData]
    total_balance: int
    salary_transactions: list[TransactionData]
    session_duration_seconds: Optional[float]
    device_type: Optional[str]
    device_model: Optional[str]

    @staticmethod
    def from_pages(loan_reference: str, pages: list[PageData]) -> PackageData:
        seen_account_numbers: set[str] = set()
        deduped_accounts: list[AccountData] = []
        all_transactions: list[TransactionData] = []
        applicant_name: Optional[str] = None
        employee_name: Optional[str] = None
        employee_id: Optional[str] = None
        device_type: Optional[str] = None
        device_model: Optional[str] = None
        timestamps: list[datetime] = []

        for page in pages:
            # Badge: take first non-None badge name and employee_id
            if page.badge is not None:
                if employee_name is None and page.badge.name is not None:
                    employee_name = page.badge.name
                if employee_id is None and page.badge.employee_id is not None:
                    employee_id = page.badge.employee_id

            # Accounts: deduplicate by account number
            for account in page.accounts:
                if account.number not in seen_account_numbers:
                    seen_account_numbers.add(account.number)
                    deduped_accounts.append(account)
                    # Take first holder_name as applicant
                    if applicant_name is None and account.holder_name is not None:
                        applicant_name = account.holder_name

            # Transactions: collect all
            all_transactions = [*all_transactions, *page.transactions]

            # Device info: first non-None wins
            if device_type is None and page.device_type is not None:
                device_type = page.device_type
            if device_model is None and page.device_model is not None:
                device_model = page.device_model

            # Timestamps for session duration
            if page.photo_timestamp is not None:
                try:
                    timestamps.append(datetime.fromisoformat(page.photo_timestamp))
                except ValueError:
                    pass

        total_balance = sum(a.balance for a in deduped_accounts)
        salary_transactions = [t for t in all_transactions if t.is_salary]

        session_duration: Optional[float] = None
        if len(timestamps) >= 2:
            earliest = min(timestamps)
            latest = max(timestamps)
            session_duration = (latest - earliest).total_seconds()

        return PackageData(
            loan_reference=loan_reference,
            pages=pages,
            applicant_name=applicant_name,
            employee_name=employee_name,
            employee_id=employee_id,
            accounts=deduped_accounts,
            transactions=all_transactions,
            total_balance=total_balance,
            salary_transactions=salary_transactions,
            session_duration_seconds=session_duration,
            device_type=device_type,
            device_model=device_model,
        )


@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_name: str
    severity: str
    description: str
    evidence: str
    page_reference: Optional[str]


@dataclass(frozen=True)
class FraudAssessment:
    loan_reference: str
    risk_score: int
    verdict: str
    package: PackageData
    findings: list[Finding]
    extraction_provider: str
    timestamp: str
