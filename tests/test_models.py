from __future__ import annotations

import dataclasses

import pytest

from pipeline.models import (
    AccountData,
    BadgeData,
    Finding,
    FraudAssessment,
    PackageData,
    PageData,
    TransactionData,
)


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestFrozenImmutability:
    def test_badge_data_is_frozen(self, sample_badge: BadgeData) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_badge.name = "mutated"  # type: ignore[misc]

    def test_account_data_is_frozen(self, sample_account: AccountData) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_account.balance = 0  # type: ignore[misc]

    def test_transaction_data_is_frozen(
        self, sample_salary_transaction: TransactionData
    ) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_salary_transaction.amount = 0  # type: ignore[misc]

    def test_page_data_is_frozen(self, sample_page_data: PageData) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_page_data.page_number = 99  # type: ignore[misc]

    def test_package_data_is_frozen(self, sample_package_data: PackageData) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_package_data.loan_reference = "mutated"  # type: ignore[misc]

    def test_finding_is_frozen(self) -> None:
        finding = Finding(
            rule_id="R001",
            rule_name="Duplicate Account",
            severity="HIGH",
            description="Account appears multiple times",
            evidence="account 2020108285007",
            page_reference="page_1",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            finding.severity = "LOW"  # type: ignore[misc]

    def test_fraud_assessment_is_frozen(
        self, sample_package_data: PackageData
    ) -> None:
        assessment = FraudAssessment(
            loan_reference="LOAN-2024-00123",
            risk_score=45,
            verdict="MEDIUM_RISK",
            package=sample_package_data,
            findings=[],
            extraction_provider="gemini-2.0-flash",
            timestamp="2024-04-01T12:00:00",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            assessment.risk_score = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestBadgeDataConstruction:
    def test_all_fields_set(self, sample_badge: BadgeData) -> None:
        assert sample_badge.name == "Doãn Thùy Hằng"
        assert sample_badge.employee_id == "42589"
        assert sample_badge.visible is True
        assert sample_badge.confidence == 0.97

    def test_optional_fields_can_be_none(self) -> None:
        badge = BadgeData(name=None, employee_id=None, visible=False, confidence=0.0)
        assert badge.name is None
        assert badge.employee_id is None


class TestAccountDataConstruction:
    def test_all_fields_set(self, sample_account: AccountData) -> None:
        assert sample_account.number == "2020108285007"
        assert sample_account.holder_name == "LE THI PHUONG"
        assert sample_account.balance == 78129696
        assert sample_account.currency == "VND"
        assert sample_account.type == "CHECKING"
        assert sample_account.is_default is True

    def test_holder_name_can_be_none(self) -> None:
        account = AccountData(
            number="1234567890",
            holder_name=None,
            balance=0,
            currency="VND",
            type="SAVINGS",
            is_default=False,
        )
        assert account.holder_name is None


class TestTransactionDataConstruction:
    def test_salary_transaction(
        self, sample_salary_transaction: TransactionData
    ) -> None:
        assert sample_salary_transaction.amount == 10184345
        assert sample_salary_transaction.direction == "CREDIT"
        assert sample_salary_transaction.is_salary is True

    def test_optional_fields_can_be_none(self) -> None:
        txn = TransactionData(
            amount=500000,
            direction="DEBIT",
            counterparty=None,
            description=None,
            timestamp=None,
            reference=None,
            is_salary=False,
        )
        assert txn.counterparty is None
        assert txn.reference is None


class TestPageDataConstruction:
    def test_all_fields_set(self, sample_page_data: PageData) -> None:
        assert sample_page_data.page_number == 1
        assert sample_page_data.screen_type == "BANK_STATEMENT"
        assert sample_page_data.confidence == 0.95
        assert sample_page_data.has_metadata is True
        assert sample_page_data.badge is not None
        assert len(sample_page_data.accounts) == 1
        assert len(sample_page_data.transactions) == 1

    def test_badge_can_be_none(self) -> None:
        page = PageData(
            page_number=2,
            screen_type="UNKNOWN",
            confidence=0.1,
            badge=None,
            accounts=[],
            transactions=[],
            device_type=None,
            device_model=None,
            photo_timestamp=None,
            photo_location=None,
            has_metadata=False,
            background_document_type=None,
        )
        assert page.badge is None


# ---------------------------------------------------------------------------
# PackageData.from_pages
# ---------------------------------------------------------------------------


class TestPackageDataFromPages:
    def test_loan_reference_preserved(
        self, sample_package_data: PackageData
    ) -> None:
        assert sample_package_data.loan_reference == "LOAN-2024-00123"

    def test_accounts_deduplicated(
        self,
        sample_page_data: PageData,
        sample_account: AccountData,
    ) -> None:
        # Two pages with the same account — should appear only once
        package = PackageData.from_pages(
            loan_reference="LOAN-DUP",
            pages=[sample_page_data, sample_page_data],
        )
        account_numbers = [a.number for a in package.accounts]
        assert account_numbers.count(sample_account.number) == 1

    def test_transactions_collected(self, sample_package_data: PackageData) -> None:
        assert len(sample_package_data.transactions) == 1

    def test_salary_transactions_filtered(
        self, sample_package_data: PackageData
    ) -> None:
        assert len(sample_package_data.salary_transactions) == 1
        assert sample_package_data.salary_transactions[0].is_salary is True

    def test_employee_name_extracted_from_badge(
        self, sample_package_data: PackageData
    ) -> None:
        assert sample_package_data.employee_name == "Doãn Thùy Hằng"

    def test_employee_id_extracted_from_badge(
        self, sample_package_data: PackageData
    ) -> None:
        assert sample_package_data.employee_id == "42589"

    def test_applicant_name_extracted_from_account(
        self, sample_package_data: PackageData
    ) -> None:
        assert sample_package_data.applicant_name == "LE THI PHUONG"

    def test_total_balance_summed(self, sample_package_data: PackageData) -> None:
        assert sample_package_data.total_balance == 78129696

    def test_session_duration_computed_single_timestamp(
        self, sample_package_data: PackageData
    ) -> None:
        # Single page → no duration (None or 0.0)
        assert sample_package_data.session_duration_seconds is None

    def test_session_duration_computed_multiple_timestamps(
        self, sample_page_data: PageData
    ) -> None:
        page2 = PageData(
            page_number=2,
            screen_type="BANK_STATEMENT",
            confidence=0.90,
            badge=None,
            accounts=[],
            transactions=[],
            device_type="ANDROID",
            device_model="Samsung Galaxy S23",
            photo_timestamp="2024-04-01T10:35:00",  # 5 minutes later
            photo_location=None,
            has_metadata=True,
            background_document_type=None,
        )
        package = PackageData.from_pages(
            loan_reference="LOAN-DUR",
            pages=[sample_page_data, page2],
        )
        assert package.session_duration_seconds == pytest.approx(300.0, abs=1.0)

    def test_device_type_extracted(self, sample_package_data: PackageData) -> None:
        assert sample_package_data.device_type == "ANDROID"

    def test_device_model_extracted(self, sample_package_data: PackageData) -> None:
        assert sample_package_data.device_model == "Samsung Galaxy S23"

    def test_empty_pages(self) -> None:
        package = PackageData.from_pages(loan_reference="LOAN-EMPTY", pages=[])
        assert package.accounts == []
        assert package.transactions == []
        assert package.total_balance == 0
        assert package.applicant_name is None
        assert package.employee_name is None


# ---------------------------------------------------------------------------
# FraudAssessment construction
# ---------------------------------------------------------------------------


class TestFraudAssessmentConstruction:
    def test_construction(self, sample_package_data: PackageData) -> None:
        finding = Finding(
            rule_id="R002",
            rule_name="Salary Mismatch",
            severity="MEDIUM",
            description="Declared salary does not match deposits",
            evidence="Expected 15000000 VND, found 10184345 VND",
            page_reference="page_1",
        )
        assessment = FraudAssessment(
            loan_reference="LOAN-2024-00123",
            risk_score=60,
            verdict="HIGH_RISK",
            package=sample_package_data,
            findings=[finding],
            extraction_provider="gemini-2.0-flash",
            timestamp="2024-04-01T12:00:00",
        )
        assert assessment.loan_reference == "LOAN-2024-00123"
        assert assessment.risk_score == 60
        assert assessment.verdict == "HIGH_RISK"
        assert len(assessment.findings) == 1
        assert assessment.findings[0].rule_id == "R002"
        assert assessment.extraction_provider == "gemini-2.0-flash"

    def test_findings_can_be_empty(self, sample_package_data: PackageData) -> None:
        assessment = FraudAssessment(
            loan_reference="LOAN-CLEAN",
            risk_score=5,
            verdict="LOW_RISK",
            package=sample_package_data,
            findings=[],
            extraction_provider="gemini-2.0-flash",
            timestamp="2024-04-01T12:00:00",
        )
        assert assessment.findings == []
