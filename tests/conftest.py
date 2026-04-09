from __future__ import annotations

import pytest

from pipeline.models import (
    AccountData,
    BadgeData,
    PageData,
    PackageData,
    TransactionData,
)


@pytest.fixture
def sample_badge() -> BadgeData:
    return BadgeData(
        name="Doãn Thùy Hằng",
        employee_id="42589",
        visible=True,
        confidence=0.97,
    )


@pytest.fixture
def sample_account() -> AccountData:
    return AccountData(
        number="2020108285007",
        holder_name="LE THI PHUONG",
        balance=78129696,
        currency="VND",
        type="CHECKING",
        is_default=True,
    )


@pytest.fixture
def sample_salary_transaction() -> TransactionData:
    return TransactionData(
        amount=10184345,
        direction="CREDIT",
        counterparty="CONG TY TNHH ABC",
        description="Luong thang 03/2024",
        timestamp="2024-03-25T09:00:00",
        reference="SAL20240325001",
        is_salary=True,
    )


@pytest.fixture
def sample_page_data(
    sample_badge: BadgeData,
    sample_account: AccountData,
    sample_salary_transaction: TransactionData,
) -> PageData:
    return PageData(
        page_number=1,
        screen_type="BANK_STATEMENT",
        confidence=0.95,
        badge=sample_badge,
        accounts=[sample_account],
        transactions=[sample_salary_transaction],
        device_type="ANDROID",
        device_model="Samsung Galaxy S23",
        photo_timestamp="2024-04-01T10:30:00",
        photo_location="21.0285,105.8542",
        has_metadata=True,
        background_document_type=None,
    )


@pytest.fixture
def sample_package_data(sample_page_data: PageData) -> PackageData:
    return PackageData.from_pages(
        loan_reference="LOAN-2024-00123",
        pages=[sample_page_data],
    )
