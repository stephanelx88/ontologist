# Neo Fraud Detection Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full autonomous fraud detection pipeline — PDF in, scored assessment + knowledge graph out — with CLI, Claude Code skill, and web app interfaces.

**Architecture:** Python package `pipeline/` is the shared engine. Gemini Vision (primary) + Claude Vision (fallback) for page extraction. Pure Python rule engine + scoring. FastAPI web app with SSE progress. All data models are frozen dataclasses.

**Tech Stack:** Python 3.12, google-genai, anthropic, PyMuPDF, FastAPI, uvicorn, pyyaml, pydantic, graphifyy, pytest

---

## File Map

```
pipeline/
├── __init__.py          # Task 1: package init
├── models.py            # Task 2: frozen dataclasses for all data
├── vision.py            # Task 3: Gemini primary + Claude fallback
├── extract.py           # Task 4: PDF → pages → vision → PackageData
├── rules.py             # Task 5: YAML rule loading + evaluation
├── score.py             # Task 6: fraud scoring + verdict
├── report.py            # Task 7: JSON + markdown report generation
├── graph.py             # Task 8: graphify integration
├── cli.py               # Task 9: CLI entry point
├── server.py            # Task 10: FastAPI web app
├── config.yaml          # Task 1: default configuration
└── templates/
    └── index.html       # Task 10: drag & drop UI

tests/
├── conftest.py          # Task 2: shared fixtures
├── test_models.py       # Task 2: model tests
├── test_vision.py       # Task 3: vision provider tests
├── test_extract.py      # Task 4: extraction tests
├── test_rules.py        # Task 5: rule evaluation tests
├── test_score.py        # Task 6: scoring tests
├── test_report.py       # Task 7: report generation tests
└── test_cli.py          # Task 9: CLI tests

pyproject.toml           # Task 1: project config + dependencies
Dockerfile               # Task 11: container
```

---

### Task 1: Project Setup + Models Foundation

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/config.yaml`
- Create: `pyproject.toml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "neo-fraud-pipeline"
version = "0.1.0"
description = "Autonomous fraud detection for Vietnamese bank statement verification"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "google-genai>=1.0.0",
    "PyMuPDF>=1.24.0",
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "pyyaml>=6.0",
    "graphifyy>=0.1.0",
    "pydantic>=2.0",
    "python-multipart",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24.0"]

[project.scripts]
neo-fraud = "pipeline.cli:main"
```

- [ ] **Step 2: Create pipeline/__init__.py**

```python
"""Neo Fraud Detection Pipeline — autonomous bank statement verification."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create pipeline/config.yaml**

```yaml
vision:
  primary: gemini
  fallback: claude
  gemini_model: gemini-2.0-flash
  claude_model: claude-sonnet-4-20250514
  confidence_threshold: 0.7

rules:
  path: workspaces/finance-and-banking/ontology/rules/fraud-detection-rules.yaml

scoring:
  critical_base: 70
  critical_additional: 10
  warning_weight: 10
  info_weight: 3
  thresholds:
    clean: 30
    review: 60

output:
  formats:
    - json
    - markdown
    - graph
```

- [ ] **Step 4: Install and verify**

```bash
pip install -e ".[dev]" && python -c "import pipeline; print(pipeline.__version__)"
```

Expected: `0.1.0`

- [ ] **Step 5: Commit**

```bash
git add pipeline/__init__.py pipeline/config.yaml pyproject.toml
git commit -m "feat: initialize pipeline package with dependencies"
```

---

### Task 2: Data Models

**Files:**
- Create: `pipeline/models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write test_models.py**

```python
"""Tests for pipeline data models — immutability and construction."""
from pipeline.models import (
    BadgeData, AccountData, TransactionData, PageData,
    PackageData, Finding, FraudAssessment,
)


def test_badge_data_is_frozen():
    badge = BadgeData(name="Doãn Thùy Hằng", employee_id="42589", visible=True, confidence=0.95)
    assert badge.name == "Doãn Thùy Hằng"
    assert badge.employee_id == "42589"
    try:
        badge.name = "changed"
        assert False, "Should not allow mutation"
    except AttributeError:
        pass


def test_account_data_construction():
    account = AccountData(
        number="2020108285007",
        holder_name="LE THI PHUONG",
        balance=78129696,
        currency="VND",
        type="payment",
        is_default=True,
    )
    assert account.balance == 78129696
    assert account.type == "payment"


def test_transaction_data_salary_flag():
    txn = TransactionData(
        amount=10184345,
        direction="incoming",
        counterparty="28 HUNG PHU JOINT FUND COMPANY",
        description="Thanh toán lương kỳ 1 tháng 01 năm 2025",
        timestamp="2025-01-10T00:00:00",
        reference="T54544W919Y010059",
        is_salary=True,
    )
    assert txn.is_salary is True
    assert txn.amount == 10184345


def test_finding_construction():
    finding = Finding(
        rule_id="name-mismatch-check",
        rule_name="Account holder name vs applicant name mismatch",
        severity="critical",
        description="Name on app does not match applicant",
        evidence="App shows NGUYEN BICH HANH, form shows different name",
        page_reference="page 3",
    )
    assert finding.severity == "critical"
    assert finding.rule_id == "name-mismatch-check"


def test_page_data_defaults():
    page = PageData(
        page_number=1,
        screen_type="home",
        confidence=0.92,
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
    assert page.page_number == 1
    assert page.accounts == []


def test_package_data_from_pages(sample_page_data):
    pkg = PackageData.from_pages(
        loan_reference="LN2501104785157",
        pages=[sample_page_data],
    )
    assert pkg.loan_reference == "LN2501104785157"
    assert len(pkg.pages) == 1
    assert pkg.applicant_name == "LE THI PHUONG"
    assert pkg.total_balance == 78129696


def test_fraud_assessment_construction(sample_package_data):
    assessment = FraudAssessment(
        loan_reference="LN2501104785157",
        risk_score=8,
        verdict="CLEAN",
        package=sample_package_data,
        findings=[],
        extraction_provider="gemini",
        timestamp="2026-04-09T21:00:00Z",
    )
    assert assessment.verdict == "CLEAN"
    assert assessment.risk_score == 8
```

- [ ] **Step 2: Write conftest.py with shared fixtures**

```python
"""Shared test fixtures for pipeline tests."""
import pytest
from pipeline.models import (
    BadgeData, AccountData, TransactionData, PageData, PackageData,
)


@pytest.fixture
def sample_badge():
    return BadgeData(
        name="Doãn Thùy Hằng",
        employee_id="42589",
        visible=True,
        confidence=0.95,
    )


@pytest.fixture
def sample_account():
    return AccountData(
        number="2020108285007",
        holder_name="LE THI PHUONG",
        balance=78129696,
        currency="VND",
        type="payment",
        is_default=True,
    )


@pytest.fixture
def sample_salary_transaction():
    return TransactionData(
        amount=10184345,
        direction="incoming",
        counterparty="28 HUNG PHU JOINT FUND COMPANY",
        description="Thanh toán lương kỳ 1 tháng 01 năm 2025",
        timestamp="2025-01-10T00:00:00",
        reference="T54544W919Y010059",
        is_salary=True,
    )


@pytest.fixture
def sample_page_data(sample_badge, sample_account, sample_salary_transaction):
    return PageData(
        page_number=1,
        screen_type="account_detail",
        confidence=0.92,
        badge=sample_badge,
        accounts=[sample_account],
        transactions=[sample_salary_transaction],
        device_type="iphone",
        device_model="iPhone SE",
        photo_timestamp=None,
        photo_location=None,
        has_metadata=False,
        background_document_type="vpbank_application_form",
    )


@pytest.fixture
def sample_package_data(sample_page_data):
    return PackageData.from_pages(
        loan_reference="LN2501104785157",
        pages=[sample_page_data],
    )
```

- [ ] **Step 3: Run tests — should FAIL**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.models'`

- [ ] **Step 4: Implement models.py**

```python
"""Frozen data models for the fraud detection pipeline."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeData:
    name: str | None
    employee_id: str | None
    visible: bool
    confidence: float


@dataclass(frozen=True)
class AccountData:
    number: str
    holder_name: str | None
    balance: int
    currency: str
    type: str
    is_default: bool


@dataclass(frozen=True)
class TransactionData:
    amount: int
    direction: str
    counterparty: str | None
    description: str | None
    timestamp: str | None
    reference: str | None
    is_salary: bool


@dataclass(frozen=True)
class PageData:
    page_number: int
    screen_type: str
    confidence: float
    badge: BadgeData | None
    accounts: list[AccountData]
    transactions: list[TransactionData]
    device_type: str | None
    device_model: str | None
    photo_timestamp: str | None
    photo_location: str | None
    has_metadata: bool
    background_document_type: str | None


@dataclass(frozen=True)
class PackageData:
    loan_reference: str
    pages: list[PageData]
    applicant_name: str | None
    employee_name: str | None
    employee_id: str | None
    accounts: list[AccountData]
    transactions: list[TransactionData]
    total_balance: int
    salary_transactions: list[TransactionData]
    session_duration_seconds: float | None
    device_type: str | None
    device_model: str | None

    @staticmethod
    def from_pages(loan_reference: str, pages: list[PageData]) -> PackageData:
        all_accounts: list[AccountData] = []
        all_transactions: list[TransactionData] = []
        seen_accounts: set[str] = set()
        applicant_name: str | None = None
        employee_name: str | None = None
        employee_id: str | None = None
        device_type: str | None = None
        device_model: str | None = None
        timestamps: list[str] = []

        for page in pages:
            for acct in page.accounts:
                if acct.number not in seen_accounts:
                    seen_accounts.add(acct.number)
                    all_accounts.append(acct)
                    if applicant_name is None and acct.holder_name:
                        applicant_name = acct.holder_name

            all_transactions.extend(page.transactions)

            if page.badge and employee_name is None:
                employee_name = page.badge.name
                employee_id = page.badge.employee_id

            if page.device_type and device_type is None:
                device_type = page.device_type
                device_model = page.device_model

            if page.photo_timestamp:
                timestamps.append(page.photo_timestamp)

        total_balance = sum(a.balance for a in all_accounts)
        salary_transactions = [t for t in all_transactions if t.is_salary]

        session_duration: float | None = None
        if len(timestamps) >= 2:
            from datetime import datetime
            try:
                parsed = sorted(datetime.fromisoformat(t) for t in timestamps)
                session_duration = (parsed[-1] - parsed[0]).total_seconds()
            except (ValueError, TypeError):
                session_duration = None

        return PackageData(
            loan_reference=loan_reference,
            pages=pages,
            applicant_name=applicant_name,
            employee_name=employee_name,
            employee_id=employee_id,
            accounts=all_accounts,
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
    page_reference: str | None


@dataclass(frozen=True)
class FraudAssessment:
    loan_reference: str
    risk_score: int
    verdict: str
    package: PackageData
    findings: list[Finding]
    extraction_provider: str
    timestamp: str
```

- [ ] **Step 5: Run tests — should PASS**

```bash
pytest tests/test_models.py -v
```

Expected: all 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add pipeline/models.py tests/conftest.py tests/test_models.py
git commit -m "feat: add frozen data models for fraud detection pipeline"
```

---

### Task 3: Vision Providers (Gemini + Claude)

**Files:**
- Create: `pipeline/vision.py`
- Create: `tests/test_vision.py`

- [ ] **Step 1: Write test_vision.py**

```python
"""Tests for vision providers — mock API calls, test parsing."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.vision import GeminiVision, ClaudeVision, extract_with_fallback
from pipeline.models import PageData


SAMPLE_VISION_RESPONSE = {
    "page_number": 1,
    "screen_type": "account_detail",
    "confidence": 0.92,
    "badge": {"name": "Doãn Thùy Hằng", "employee_id": "42589", "visible": True, "confidence": 0.95},
    "accounts": [{"number": "2020108285007", "holder_name": "LE THI PHUONG", "balance": 78129696, "currency": "VND", "type": "payment", "is_default": True}],
    "transactions": [{"amount": 10184345, "direction": "incoming", "counterparty": "28 HUNG PHU JOINT FUND COMPANY", "description": "Thanh toán lương kỳ 1 tháng 01 năm 2025", "timestamp": "2025-01-10T00:00:00", "reference": "T54544W919Y010059", "is_salary": True}],
    "device": {"type": "iphone", "model": "iPhone SE"},
    "photo_metadata": {"timestamp": None, "location": None, "has_metadata": False},
    "background_document": {"visible": True, "type": "vpbank_application_form"}
}


def test_parse_vision_response_to_page_data():
    from pipeline.vision import parse_vision_response
    page = parse_vision_response(SAMPLE_VISION_RESPONSE)
    assert isinstance(page, PageData)
    assert page.screen_type == "account_detail"
    assert page.badge.name == "Doãn Thùy Hằng"
    assert page.accounts[0].balance == 78129696
    assert page.transactions[0].is_salary is True


def test_parse_vision_response_missing_fields():
    from pipeline.vision import parse_vision_response
    minimal = {"page_number": 1, "screen_type": "unknown", "confidence": 0.3}
    page = parse_vision_response(minimal)
    assert page.page_number == 1
    assert page.badge is None
    assert page.accounts == []
    assert page.transactions == []


def test_parse_vision_response_bad_json():
    from pipeline.vision import parse_vision_response
    page = parse_vision_response({})
    assert page.page_number == 0
    assert page.confidence == 0.0


@pytest.mark.asyncio
async def test_gemini_extract_page_calls_api():
    gemini = GeminiVision(api_key="test-key", model="gemini-2.0-flash")
    with patch.object(gemini, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = SAMPLE_VISION_RESPONSE
        page = await gemini.extract_page(b"fake-image-bytes", page_number=1)
        assert page.screen_type == "account_detail"
        mock_api.assert_called_once()


@pytest.mark.asyncio
async def test_claude_extract_page_calls_api():
    claude = ClaudeVision(api_key="test-key", model="claude-sonnet-4-20250514")
    with patch.object(claude, '_call_api', new_callable=AsyncMock) as mock_api:
        mock_api.return_value = SAMPLE_VISION_RESPONSE
        page = await claude.extract_page(b"fake-image-bytes", page_number=1)
        assert page.badge.employee_id == "42589"
        mock_api.assert_called_once()


@pytest.mark.asyncio
async def test_fallback_triggered_on_low_confidence():
    gemini = GeminiVision(api_key="test-key", model="gemini-2.0-flash")
    claude = ClaudeVision(api_key="test-key", model="claude-sonnet-4-20250514")

    low_confidence = {**SAMPLE_VISION_RESPONSE, "confidence": 0.4, "badge": {"name": None, "employee_id": None, "visible": False, "confidence": 0.2}}
    high_confidence = SAMPLE_VISION_RESPONSE

    with patch.object(gemini, '_call_api', new_callable=AsyncMock, return_value=low_confidence), \
         patch.object(claude, '_call_api', new_callable=AsyncMock, return_value=high_confidence):
        page = await extract_with_fallback(b"image", 1, gemini, claude, threshold=0.7)
        assert page.badge.name == "Doãn Thùy Hằng"
        assert page.confidence == 0.92


@pytest.mark.asyncio
async def test_no_fallback_when_confident():
    gemini = GeminiVision(api_key="test-key", model="gemini-2.0-flash")
    claude = ClaudeVision(api_key="test-key", model="claude-sonnet-4-20250514")

    with patch.object(gemini, '_call_api', new_callable=AsyncMock, return_value=SAMPLE_VISION_RESPONSE), \
         patch.object(claude, '_call_api', new_callable=AsyncMock) as claude_mock:
        page = await extract_with_fallback(b"image", 1, gemini, claude, threshold=0.7)
        assert page.confidence == 0.92
        claude_mock.assert_not_called()
```

- [ ] **Step 2: Run tests — should FAIL**

```bash
pytest tests/test_vision.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.vision'`

- [ ] **Step 3: Implement vision.py**

```python
"""Vision extraction providers — Gemini primary, Claude fallback."""
from __future__ import annotations

import base64
import json
from pipeline.models import (
    PageData, BadgeData, AccountData, TransactionData,
)

EXTRACTION_PROMPT = """Analyze this bank statement verification photo. Extract ALL visible data into structured JSON.

This is a photograph of a Vietnamese mobile banking app screen (likely MBBank) taken alongside a VPBank employee badge during a loan application verification process.

Return ONLY valid JSON matching this exact schema:
{
  "page_number": PAGE_NUM,
  "screen_type": "home | qr | account_list | account_detail | transaction_detail | unknown",
  "confidence": 0.0-1.0,
  "badge": {"name": "full name or null", "employee_id": "numeric string or null", "visible": true/false, "confidence": 0.0-1.0},
  "accounts": [{"number": "string", "holder_name": "string or null", "balance": integer_vnd, "currency": "VND", "type": "payment|overdraft|foreign_currency", "is_default": true/false}],
  "transactions": [{"amount": integer_vnd, "direction": "incoming|outgoing", "counterparty": "string or null", "description": "string or null", "timestamp": "ISO datetime or null", "reference": "string or null", "is_salary": true/false}],
  "device": {"type": "iphone|samsung|other", "model": "description or null"},
  "photo_metadata": {"timestamp": "ISO datetime or null", "location": "string or null", "has_metadata": true/false},
  "background_document": {"visible": true/false, "type": "vpbank_application_form|other|null"}
}

Rules:
- Vietnamese text: preserve diacritics exactly (ã, ắ, ừ, etc.)
- Balance/amounts: integers in VND, no decimals
- is_salary: true if description contains "lương", "luong", "Luong", or "salary"
- confidence: your certainty about the overall extraction quality
- If text is blurry/unreadable, set the field to null and lower confidence
- Do NOT guess — null is better than wrong"""


def parse_vision_response(data: dict) -> PageData:
    """Parse raw vision API response into a PageData model."""
    badge_raw = data.get("badge")
    badge = None
    if badge_raw and badge_raw.get("visible"):
        badge = BadgeData(
            name=badge_raw.get("name"),
            employee_id=badge_raw.get("employee_id"),
            visible=badge_raw.get("visible", False),
            confidence=badge_raw.get("confidence", 0.0),
        )

    accounts = []
    for a in data.get("accounts", []):
        accounts.append(AccountData(
            number=a.get("number", ""),
            holder_name=a.get("holder_name"),
            balance=int(a.get("balance", 0)),
            currency=a.get("currency", "VND"),
            type=a.get("type", "payment"),
            is_default=a.get("is_default", False),
        ))

    transactions = []
    for t in data.get("transactions", []):
        transactions.append(TransactionData(
            amount=int(t.get("amount", 0)),
            direction=t.get("direction", "incoming"),
            counterparty=t.get("counterparty"),
            description=t.get("description"),
            timestamp=t.get("timestamp"),
            reference=t.get("reference"),
            is_salary=t.get("is_salary", False),
        ))

    device = data.get("device", {})
    meta = data.get("photo_metadata", {})
    bg = data.get("background_document", {})

    return PageData(
        page_number=data.get("page_number", 0),
        screen_type=data.get("screen_type", "unknown"),
        confidence=data.get("confidence", 0.0),
        badge=badge,
        accounts=accounts,
        transactions=transactions,
        device_type=device.get("type"),
        device_model=device.get("model"),
        photo_timestamp=meta.get("timestamp"),
        photo_location=meta.get("location"),
        has_metadata=meta.get("has_metadata", False),
        background_document_type=bg.get("type") if bg.get("visible") else None,
    )


class GeminiVision:
    """Primary vision provider — Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def _call_api(self, image_bytes: bytes, page_number: int) -> dict:
        from google import genai
        client = genai.Client(api_key=self.api_key)
        prompt = EXTRACTION_PROMPT.replace("PAGE_NUM", str(page_number))
        response = client.models.generate_content(
            model=self.model,
            contents=[
                {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(image_bytes).decode()}},
                prompt,
            ],
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def extract_page(self, image_bytes: bytes, page_number: int) -> PageData:
        data = await self._call_api(image_bytes, page_number)
        return parse_vision_response(data)


class ClaudeVision:
    """Fallback vision provider — Claude API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model

    async def _call_api(self, image_bytes: bytes, page_number: int) -> dict:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        prompt = EXTRACTION_PROMPT.replace("PAGE_NUM", str(page_number))
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(image_bytes).decode()}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def extract_page(self, image_bytes: bytes, page_number: int) -> PageData:
        data = await self._call_api(image_bytes, page_number)
        return parse_vision_response(data)


async def extract_with_fallback(
    image_bytes: bytes,
    page_number: int,
    primary: GeminiVision,
    fallback: ClaudeVision,
    threshold: float = 0.7,
) -> PageData:
    """Extract with primary provider, fall back if confidence is low."""
    page = await primary.extract_page(image_bytes, page_number)
    if page.confidence >= threshold:
        return page
    fallback_page = await fallback.extract_page(image_bytes, page_number)
    if fallback_page.confidence > page.confidence:
        return fallback_page
    return page
```

- [ ] **Step 4: Run tests — should PASS**

```bash
pytest tests/test_vision.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/vision.py tests/test_vision.py
git commit -m "feat: add Gemini + Claude vision providers with fallback"
```

---

### Task 4: PDF Extraction Pipeline

**Files:**
- Create: `pipeline/extract.py`
- Create: `tests/test_extract.py`

- [ ] **Step 1: Write test_extract.py**

```python
"""Tests for PDF extraction pipeline."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from pipeline.extract import split_pdf_to_images, extract_package
from pipeline.models import PackageData


def test_split_pdf_to_images(tmp_path):
    """Test with a minimal valid PDF — or skip if no test PDF available."""
    # Create a trivial 1-page PDF for testing
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    page.insert_text((50, 100), "test page")
    pdf_path = tmp_path / "test.pdf"
    doc.save(str(pdf_path))
    doc.close()

    images = split_pdf_to_images(pdf_path)
    assert len(images) == 1
    assert isinstance(images[0], bytes)
    assert len(images[0]) > 100  # PNG has content


def test_split_pdf_multiple_pages(tmp_path):
    import fitz
    doc = fitz.open()
    for i in range(5):
        page = doc.new_page(width=200, height=200)
        page.insert_text((50, 100), f"page {i+1}")
    pdf_path = tmp_path / "multi.pdf"
    doc.save(str(pdf_path))
    doc.close()

    images = split_pdf_to_images(pdf_path)
    assert len(images) == 5


def test_extract_loan_reference_from_filename():
    from pipeline.extract import extract_loan_reference
    assert extract_loan_reference("MBBbank- mobile app -mã LN2501104785157.pdf") == "LN2501104785157"
    assert extract_loan_reference("some-file.pdf") == "UNKNOWN"
    assert extract_loan_reference("LN2501134790716.pdf") == "LN2501134790716"


@pytest.mark.asyncio
async def test_extract_package_merges_pages():
    from pipeline.vision import GeminiVision, ClaudeVision
    from tests.test_vision import SAMPLE_VISION_RESPONSE

    gemini = GeminiVision(api_key="test")
    claude = ClaudeVision(api_key="test")

    with patch.object(gemini, '_call_api', new_callable=AsyncMock, return_value=SAMPLE_VISION_RESPONSE), \
         patch('pipeline.extract.split_pdf_to_images', return_value=[b"img1", b"img2"]):
        pkg = await extract_package(
            pdf_path=Path("test.pdf"),
            primary=gemini,
            fallback=claude,
            confidence_threshold=0.7,
        )
        assert isinstance(pkg, PackageData)
        assert len(pkg.pages) == 2
        assert pkg.applicant_name == "LE THI PHUONG"
```

- [ ] **Step 2: Run tests — should FAIL**

```bash
pytest tests/test_extract.py -v
```

- [ ] **Step 3: Implement extract.py**

```python
"""PDF extraction — split pages, run vision, merge into PackageData."""
from __future__ import annotations

import re
from pathlib import Path
from pipeline.models import PackageData, PageData
from pipeline.vision import GeminiVision, ClaudeVision, extract_with_fallback


def split_pdf_to_images(pdf_path: Path, dpi: int = 200) -> list[bytes]:
    """Split a PDF into PNG images, one per page."""
    import fitz
    doc = fitz.open(str(pdf_path))
    images = []
    for page in doc:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


def extract_loan_reference(filename: str) -> str:
    """Extract LN reference from filename."""
    match = re.search(r'(LN\d+)', filename)
    return match.group(1) if match else "UNKNOWN"


async def extract_package(
    pdf_path: Path,
    primary: GeminiVision,
    fallback: ClaudeVision,
    confidence_threshold: float = 0.7,
    on_progress: callable | None = None,
) -> PackageData:
    """Full extraction pipeline: PDF → pages → vision → PackageData."""
    images = split_pdf_to_images(pdf_path)
    pages: list[PageData] = []

    for i, image_bytes in enumerate(images):
        page_num = i + 1
        if on_progress:
            on_progress(f"Extracting page {page_num}/{len(images)}")
        page = await extract_with_fallback(
            image_bytes, page_num, primary, fallback, confidence_threshold,
        )
        pages.append(page)

    loan_ref = extract_loan_reference(pdf_path.name)
    return PackageData.from_pages(loan_reference=loan_ref, pages=pages)
```

- [ ] **Step 4: Run tests — should PASS**

```bash
pytest tests/test_extract.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/extract.py tests/test_extract.py
git commit -m "feat: add PDF extraction pipeline with page splitting"
```

---

### Task 5: Rule Engine

**Files:**
- Create: `pipeline/rules.py`
- Create: `tests/test_rules.py`

- [ ] **Step 1: Write test_rules.py**

```python
"""Tests for fraud detection rule engine."""
import pytest
from pipeline.rules import evaluate_all_rules, load_rules
from pipeline.models import (
    PackageData, PageData, BadgeData, AccountData, TransactionData, Finding,
)


def _make_package(
    badge_visible=True,
    badge_name="Doãn Thùy Hằng",
    badge_id="42589",
    holder_name="LE THI PHUONG",
    balance=78129696,
    salary_amount=10184345,
    salary_description="Thanh toán lương kỳ 1",
    photo_timestamps=None,
    num_pages=5,
) -> PackageData:
    badge = BadgeData(name=badge_name, employee_id=badge_id, visible=badge_visible, confidence=0.95)
    account = AccountData(number="2020108285007", holder_name=holder_name, balance=balance, currency="VND", type="payment", is_default=True)
    txn = TransactionData(amount=salary_amount, direction="incoming", counterparty="COMPANY", description=salary_description, timestamp="2025-01-10T00:00:00", reference="REF001", is_salary=True)

    pages = []
    for i in range(num_pages):
        ts = photo_timestamps[i] if photo_timestamps and i < len(photo_timestamps) else None
        pages.append(PageData(
            page_number=i + 1,
            screen_type="account_detail" if i == 0 else "home",
            confidence=0.9,
            badge=badge if badge_visible else None,
            accounts=[account] if i == 0 else [],
            transactions=[txn] if i == 0 else [],
            device_type="iphone", device_model="iPhone SE",
            photo_timestamp=ts, photo_location=None,
            has_metadata=ts is not None,
            background_document_type=None,
        ))
    return PackageData.from_pages(loan_reference="LN001", pages=pages)


def test_clean_package_no_findings():
    pkg = _make_package()
    findings = evaluate_all_rules(pkg)
    critical = [f for f in findings if f.severity == "critical"]
    assert len(critical) == 0


def test_missing_badge_is_critical():
    pkg = _make_package(badge_visible=False)
    findings = evaluate_all_rules(pkg)
    badge_findings = [f for f in findings if f.rule_id == "badge-present-check"]
    assert len(badge_findings) == 1
    assert badge_findings[0].severity == "critical"


def test_round_salary_flagged_as_info():
    pkg = _make_package(salary_amount=5000000)
    findings = evaluate_all_rules(pkg)
    round_findings = [f for f in findings if f.rule_id == "round-number-deposit"]
    assert len(round_findings) == 1
    assert round_findings[0].severity == "info"


def test_non_round_salary_not_flagged():
    pkg = _make_package(salary_amount=10184345)
    findings = evaluate_all_rules(pkg)
    round_findings = [f for f in findings if f.rule_id == "round-number-deposit"]
    assert len(round_findings) == 0


def test_high_balance_ratio_flagged():
    pkg = _make_package(balance=100000000, salary_amount=5000000)
    findings = evaluate_all_rules(pkg)
    ratio_findings = [f for f in findings if f.rule_id == "balance-vs-salary-ratio"]
    assert len(ratio_findings) == 1


def test_salary_without_keyword_flagged():
    pkg = _make_package(salary_description="TRANSFER FROM ACCOUNT")
    findings = evaluate_all_rules(pkg)
    fmt_findings = [f for f in findings if f.rule_id == "salary-description-format"]
    assert len(fmt_findings) == 1
```

- [ ] **Step 2: Run tests — should FAIL**

```bash
pytest tests/test_rules.py -v
```

- [ ] **Step 3: Implement rules.py**

```python
"""Fraud detection rule engine — pure Python, no LLM."""
from __future__ import annotations

from pipeline.models import PackageData, Finding

SALARY_KEYWORDS = ["lương", "luong", "Luong", "LUONG", "salary", "Salary"]


def evaluate_badge_present(pkg: PackageData) -> Finding | None:
    pages_without_badge = [p for p in pkg.pages if p.badge is None or not p.badge.visible]
    if pages_without_badge:
        return Finding(
            rule_id="badge-present-check",
            rule_name="Employee badge must be visible in all verification photos",
            severity="critical",
            description=f"Badge missing in {len(pages_without_badge)} of {len(pkg.pages)} pages",
            evidence=f"Pages without badge: {[p.page_number for p in pages_without_badge]}",
            page_reference=f"page {pages_without_badge[0].page_number}",
        )
    return None


def evaluate_employee_consistency(pkg: PackageData) -> Finding | None:
    ids = set()
    for p in pkg.pages:
        if p.badge and p.badge.employee_id:
            ids.add(p.badge.employee_id)
    if len(ids) > 1:
        return Finding(
            rule_id="employee-consistency-check",
            rule_name="Same employee badge across all photos in package",
            severity="critical",
            description=f"Multiple employee IDs detected: {ids}",
            evidence=f"Employee IDs found: {sorted(ids)}",
            page_reference=None,
        )
    return None


def evaluate_name_mismatch(pkg: PackageData) -> Finding | None:
    if not pkg.applicant_name:
        return None
    names = set()
    for acct in pkg.accounts:
        if acct.holder_name:
            names.add(acct.holder_name.upper().strip())
    if len(names) > 1:
        return Finding(
            rule_id="name-mismatch-check",
            rule_name="Account holder name vs applicant name mismatch",
            severity="critical",
            description=f"Multiple account holder names found: {names}",
            evidence=f"Names: {sorted(names)}",
            page_reference=None,
        )
    return None


def evaluate_balance_consistency(pkg: PackageData) -> Finding | None:
    balances_by_account: dict[str, set[int]] = {}
    for p in pkg.pages:
        for a in p.accounts:
            balances_by_account.setdefault(a.number, set()).add(a.balance)
    for acct_num, balances in balances_by_account.items():
        if len(balances) > 1:
            return Finding(
                rule_id="balance-consistency-check",
                rule_name="Balance shown in list must match detail view",
                severity="critical",
                description=f"Account {acct_num} shows different balances: {balances}",
                evidence=f"Balances: {sorted(balances)}",
                page_reference=None,
            )
    return None


def evaluate_timestamp_sequence(pkg: PackageData) -> Finding | None:
    timestamps = [p.photo_timestamp for p in pkg.pages if p.photo_timestamp]
    if len(timestamps) < 2:
        return None
    from datetime import datetime
    try:
        parsed = [datetime.fromisoformat(t) for t in timestamps]
        duration = (max(parsed) - min(parsed)).total_seconds()
        if duration > 600:  # 10 minutes
            return Finding(
                rule_id="photo-timestamp-sequence",
                rule_name="Photo timestamps must be sequential",
                severity="warning",
                description=f"Photo session spans {duration:.0f} seconds ({duration/60:.1f} min)",
                evidence=f"Earliest: {min(timestamps)}, Latest: {max(timestamps)}",
                page_reference=None,
            )
    except (ValueError, TypeError):
        pass
    return None


def evaluate_screenshot_freshness(pkg: PackageData) -> Finding | None:
    return None  # Requires comparing photo date vs app query date — vision extracts this


def evaluate_salary_description(pkg: PackageData) -> Finding | None:
    for txn in pkg.salary_transactions:
        if txn.description:
            has_keyword = any(kw in txn.description for kw in SALARY_KEYWORDS)
            if not has_keyword:
                return Finding(
                    rule_id="salary-description-format",
                    rule_name="Salary description must contain standard keywords",
                    severity="warning",
                    description=f"Salary transaction lacks standard keywords",
                    evidence=f"Description: '{txn.description}'",
                    page_reference=None,
                )
    return None


def evaluate_salary_regularity(pkg: PackageData) -> Finding | None:
    if len(pkg.salary_transactions) < 2:
        return None
    amounts = [t.amount for t in pkg.salary_transactions]
    avg = sum(amounts) / len(amounts)
    for amt in amounts:
        if abs(amt - avg) / avg > 0.5:
            return Finding(
                rule_id="salary-regularity-check",
                rule_name="Salary transactions should show regular pattern",
                severity="warning",
                description=f"Salary amount variance exceeds 50%",
                evidence=f"Amounts: {amounts}, Average: {avg:.0f}",
                page_reference=None,
            )
    return None


def evaluate_round_numbers(pkg: PackageData) -> Finding | None:
    for txn in pkg.salary_transactions:
        if txn.amount > 0 and txn.amount % 1_000_000 == 0:
            return Finding(
                rule_id="round-number-deposit",
                rule_name="Suspiciously round deposit amounts",
                severity="info",
                description=f"Salary amount is perfectly round: {txn.amount:,} VND",
                evidence=f"Amount {txn.amount:,} is divisible by 1,000,000",
                page_reference=None,
            )
    return None


def evaluate_balance_salary_ratio(pkg: PackageData) -> Finding | None:
    if not pkg.salary_transactions:
        return None
    avg_salary = sum(t.amount for t in pkg.salary_transactions) / len(pkg.salary_transactions)
    if avg_salary > 0 and pkg.total_balance > avg_salary * 6:
        ratio = pkg.total_balance / avg_salary
        return Finding(
            rule_id="balance-vs-salary-ratio",
            rule_name="Balance to salary ratio check",
            severity="info",
            description=f"Balance is {ratio:.1f}x average salary",
            evidence=f"Balance: {pkg.total_balance:,} VND, Avg salary: {avg_salary:,.0f} VND",
            page_reference=None,
        )
    return None


ALL_EVALUATORS = [
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
    """Run all fraud detection rules against a package."""
    findings = []
    for evaluator in ALL_EVALUATORS:
        result = evaluator(pkg)
        if result is not None:
            findings.append(result)
    return findings
```

- [ ] **Step 4: Run tests — should PASS**

```bash
pytest tests/test_rules.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/rules.py tests/test_rules.py
git commit -m "feat: add fraud detection rule engine with 10 evaluators"
```

---

### Task 6: Scoring

**Files:**
- Create: `pipeline/score.py`
- Create: `tests/test_score.py`

- [ ] **Step 1: Write test_score.py**

```python
"""Tests for fraud scoring."""
from pipeline.score import compute_score
from pipeline.models import Finding


def _finding(severity: str, rule_id: str = "test") -> Finding:
    return Finding(rule_id=rule_id, rule_name="Test", severity=severity, description="", evidence="", page_reference=None)


def test_no_findings_is_clean():
    score, verdict = compute_score([])
    assert score == 0
    assert verdict == "CLEAN"


def test_single_critical_is_suspicious():
    score, verdict = compute_score([_finding("critical")])
    assert score == 70
    assert verdict == "SUSPICIOUS"


def test_two_criticals():
    score, verdict = compute_score([_finding("critical"), _finding("critical")])
    assert score == 80
    assert verdict == "SUSPICIOUS"


def test_warnings_accumulate():
    score, verdict = compute_score([_finding("warning"), _finding("warning"), _finding("warning")])
    assert score == 30
    assert verdict == "CLEAN"  # exactly 30 = CLEAN


def test_four_warnings_is_review():
    score, verdict = compute_score([_finding("warning")] * 4)
    assert score == 40
    assert verdict == "REVIEW"


def test_info_only():
    score, verdict = compute_score([_finding("info"), _finding("info")])
    assert score == 6
    assert verdict == "CLEAN"


def test_cap_at_100():
    findings = [_finding("critical")] * 5 + [_finding("warning")] * 5
    score, verdict = compute_score(findings)
    assert score == 100


def test_mixed_severities():
    score, verdict = compute_score([_finding("critical"), _finding("warning"), _finding("info")])
    assert score == 83  # 70 + 10 + 3
    assert verdict == "SUSPICIOUS"
```

- [ ] **Step 2: Run tests — should FAIL**

```bash
pytest tests/test_score.py -v
```

- [ ] **Step 3: Implement score.py**

```python
"""Fraud scoring — compute risk score and verdict from findings."""
from __future__ import annotations

from pipeline.models import Finding


def compute_score(findings: list[Finding]) -> tuple[int, str]:
    """Compute fraud risk score (0-100) and verdict."""
    score = 0
    has_critical = False

    for f in findings:
        if f.severity == "critical":
            if not has_critical:
                score += 70
                has_critical = True
            else:
                score += 10
        elif f.severity == "warning":
            score += 10
        elif f.severity == "info":
            score += 3

    score = min(score, 100)

    if score >= 61:
        verdict = "SUSPICIOUS"
    elif score >= 31:
        verdict = "REVIEW"
    else:
        verdict = "CLEAN"

    return score, verdict
```

- [ ] **Step 4: Run tests — should PASS**

```bash
pytest tests/test_score.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/score.py tests/test_score.py
git commit -m "feat: add fraud scoring with CLEAN/REVIEW/SUSPICIOUS verdicts"
```

---

### Task 7: Report Generation

**Files:**
- Create: `pipeline/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1: Write test_report.py**

```python
"""Tests for report generation."""
import json
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.models import FraudAssessment, Finding


def test_json_report_is_valid_json(sample_package_data):
    assessment = FraudAssessment(
        loan_reference="LN001", risk_score=8, verdict="CLEAN",
        package=sample_package_data, findings=[], extraction_provider="gemini",
        timestamp="2026-04-09T21:00:00Z",
    )
    report = generate_json_report(assessment)
    parsed = json.loads(report)
    assert parsed["loan_reference"] == "LN001"
    assert parsed["verdict"] == "CLEAN"
    assert parsed["risk_score"] == 8


def test_json_report_includes_findings(sample_package_data):
    finding = Finding(rule_id="test", rule_name="Test", severity="info", description="Test desc", evidence="Test ev", page_reference="page 1")
    assessment = FraudAssessment(
        loan_reference="LN001", risk_score=3, verdict="CLEAN",
        package=sample_package_data, findings=[finding], extraction_provider="gemini",
        timestamp="2026-04-09T21:00:00Z",
    )
    report = generate_json_report(assessment)
    parsed = json.loads(report)
    assert len(parsed["findings"]) == 1
    assert parsed["findings"][0]["rule_id"] == "test"


def test_markdown_report_has_sections(sample_package_data):
    assessment = FraudAssessment(
        loan_reference="LN001", risk_score=8, verdict="CLEAN",
        package=sample_package_data, findings=[], extraction_provider="gemini",
        timestamp="2026-04-09T21:00:00Z",
    )
    md = generate_markdown_report(assessment)
    assert "# Fraud Assessment" in md
    assert "LN001" in md
    assert "CLEAN" in md
    assert "LE THI PHUONG" in md
```

- [ ] **Step 2: Run tests — should FAIL**

```bash
pytest tests/test_report.py -v
```

- [ ] **Step 3: Implement report.py**

```python
"""Report generation — JSON and Markdown outputs."""
from __future__ import annotations

import json
from dataclasses import asdict
from pipeline.models import FraudAssessment


def generate_json_report(assessment: FraudAssessment) -> str:
    """Generate machine-readable JSON report."""
    data = {
        "loan_reference": assessment.loan_reference,
        "risk_score": assessment.risk_score,
        "verdict": assessment.verdict,
        "extraction_provider": assessment.extraction_provider,
        "timestamp": assessment.timestamp,
        "applicant": {
            "name": assessment.package.applicant_name,
            "accounts": [{"number": a.number, "holder_name": a.holder_name, "balance": a.balance, "type": a.type} for a in assessment.package.accounts],
            "total_balance": assessment.package.total_balance,
        },
        "employee": {
            "name": assessment.package.employee_name,
            "id": assessment.package.employee_id,
        },
        "salary_summary": [
            {"amount": t.amount, "description": t.description, "timestamp": t.timestamp, "counterparty": t.counterparty}
            for t in assessment.package.salary_transactions
        ],
        "findings": [
            {"rule_id": f.rule_id, "rule_name": f.rule_name, "severity": f.severity, "description": f.description, "evidence": f.evidence, "page_reference": f.page_reference}
            for f in assessment.findings
        ],
        "pages_analyzed": len(assessment.package.pages),
        "device": {"type": assessment.package.device_type, "model": assessment.package.device_model},
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_markdown_report(assessment: FraudAssessment) -> str:
    """Generate human-readable Markdown report."""
    pkg = assessment.package
    lines = [
        f"# Fraud Assessment — {assessment.loan_reference}",
        "",
        f"**Verdict:** {assessment.verdict}",
        f"**Risk Score:** {assessment.risk_score}/100",
        f"**Timestamp:** {assessment.timestamp}",
        f"**Extraction:** {assessment.extraction_provider}",
        "",
        "---",
        "",
        "## Applicant",
        "",
        f"- **Name:** {pkg.applicant_name or 'Unknown'}",
        f"- **Total Balance:** {pkg.total_balance:,} VND",
        f"- **Device:** {pkg.device_type or 'Unknown'} ({pkg.device_model or 'Unknown'})",
    ]

    if pkg.accounts:
        lines.append("")
        lines.append("### Accounts")
        lines.append("")
        lines.append("| Account | Holder | Balance | Type |")
        lines.append("|---------|--------|---------|------|")
        for a in pkg.accounts:
            lines.append(f"| {a.number} | {a.holder_name or '—'} | {a.balance:,} VND | {a.type} |")

    lines.extend(["", "## Employee", "", f"- **Name:** {pkg.employee_name or 'Unknown'}", f"- **ID:** {pkg.employee_id or 'Unknown'}"])

    if pkg.salary_transactions:
        lines.extend(["", "## Salary Evidence", ""])
        for t in pkg.salary_transactions:
            lines.append(f"- **{t.amount:,} VND** — {t.description or 'No description'} ({t.timestamp or 'No date'})")

    lines.extend(["", "---", "", "## Findings", ""])
    if assessment.findings:
        for f in assessment.findings:
            icon = {"critical": "!!!", "warning": "!!", "info": "i"}.get(f.severity, "?")
            lines.append(f"### [{f.severity.upper()}] {f.rule_name}")
            lines.append(f"")
            lines.append(f"- **Rule:** `{f.rule_id}`")
            lines.append(f"- **Description:** {f.description}")
            lines.append(f"- **Evidence:** {f.evidence}")
            if f.page_reference:
                lines.append(f"- **Page:** {f.page_reference}")
            lines.append("")
    else:
        lines.append("No findings — all rules passed.")

    lines.extend(["", f"---", f"", f"*{len(pkg.pages)} pages analyzed*"])
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests — should PASS**

```bash
pytest tests/test_report.py -v
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/report.py tests/test_report.py
git commit -m "feat: add JSON and Markdown report generation"
```

---

### Task 8: Graphify Integration

**Files:**
- Create: `pipeline/graph.py`

- [ ] **Step 1: Implement graph.py**

```python
"""Knowledge graph generation for fraud assessments via graphify."""
from __future__ import annotations

import json
from pathlib import Path
from pipeline.models import FraudAssessment


def generate_graph_data(assessment: FraudAssessment) -> dict:
    """Generate graphify-compatible graph.json from a fraud assessment."""
    nodes = []
    edges = []
    pkg = assessment.package

    # Core nodes
    nodes.append({"id": f"package_{pkg.loan_reference}", "label": f"Package {pkg.loan_reference}", "file_type": "document", "source_file": "", "community": 0})

    if pkg.applicant_name:
        nodes.append({"id": "applicant", "label": pkg.applicant_name, "file_type": "document", "source_file": "", "community": 1})
        edges.append({"source": "applicant", "target": f"package_{pkg.loan_reference}", "relation": "submits", "confidence": "EXTRACTED", "confidence_score": 1.0})

    if pkg.employee_name:
        nodes.append({"id": f"employee_{pkg.employee_id}", "label": f"{pkg.employee_name} (ID: {pkg.employee_id})", "file_type": "document", "source_file": "", "community": 2})
        edges.append({"source": f"employee_{pkg.employee_id}", "target": f"package_{pkg.loan_reference}", "relation": "verifies", "confidence": "EXTRACTED", "confidence_score": 1.0})

    for acct in pkg.accounts:
        nid = f"account_{acct.number}"
        nodes.append({"id": nid, "label": f"{acct.number} ({acct.balance:,} VND)", "file_type": "document", "source_file": "", "community": 1})
        edges.append({"source": "applicant", "target": nid, "relation": "holds", "confidence": "EXTRACTED", "confidence_score": 1.0})

    for i, txn in enumerate(pkg.salary_transactions):
        nid = f"salary_{i}"
        nodes.append({"id": nid, "label": f"Salary: {txn.amount:,} VND", "file_type": "document", "source_file": "", "community": 3})
        if pkg.accounts:
            edges.append({"source": f"account_{pkg.accounts[0].number}", "target": nid, "relation": "contains", "confidence": "EXTRACTED", "confidence_score": 1.0})

    for f in assessment.findings:
        nid = f"finding_{f.rule_id}"
        nodes.append({"id": nid, "label": f"[{f.severity.upper()}] {f.rule_name}", "file_type": "document", "source_file": "", "community": 4})
        edges.append({"source": nid, "target": f"package_{pkg.loan_reference}", "relation": "flags", "confidence": "EXTRACTED", "confidence_score": 1.0})

    return {"nodes": nodes, "edges": edges}


def save_graph(assessment: FraudAssessment, output_dir: Path) -> Path:
    """Save graph.json and generate graph.html if graphify is available."""
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_data = generate_graph_data(assessment)
    graph_path = output_dir / "graph.json"
    graph_path.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False))

    try:
        from graphify.build import build_from_json
        from graphify.cluster import cluster
        from graphify.export import to_html, to_json
        G = build_from_json(graph_data)
        communities = cluster(G)
        to_json(G, communities, str(output_dir / "graph.json"))
        to_html(G, communities, str(output_dir / "graph.html"))
    except ImportError:
        pass  # graphify not installed — graph.json still saved

    return graph_path
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/graph.py
git commit -m "feat: add graphify knowledge graph generation"
```

---

### Task 9: CLI

**Files:**
- Create: `pipeline/cli.py`

- [ ] **Step 1: Implement cli.py**

```python
"""CLI entry point — process PDFs from the command line."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.extract import extract_package
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.graph import save_graph
from pipeline.vision import GeminiVision, ClaudeVision
from pipeline.models import FraudAssessment


async def process_single(pdf_path: Path, output_dir: Path, verbose: bool = False) -> FraudAssessment:
    """Process a single PDF and return the assessment."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if not gemini_key:
        print("Error: GEMINI_API_KEY environment variable required", file=sys.stderr)
        sys.exit(1)

    primary = GeminiVision(api_key=gemini_key)
    fallback = ClaudeVision(api_key=anthropic_key) if anthropic_key else None

    def on_progress(msg: str):
        if verbose:
            print(f"  {msg}")

    if verbose:
        print(f"Processing: {pdf_path.name}")

    pkg = await extract_package(
        pdf_path=pdf_path,
        primary=primary,
        fallback=fallback,
        confidence_threshold=0.7,
        on_progress=on_progress,
    )

    if verbose:
        print("  Running fraud rules...")

    findings = evaluate_all_rules(pkg)
    risk_score, verdict = compute_score(findings)

    assessment = FraudAssessment(
        loan_reference=pkg.loan_reference,
        risk_score=risk_score,
        verdict=verdict,
        package=pkg,
        findings=findings,
        extraction_provider="gemini" if not fallback else "hybrid",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Save outputs
    result_dir = output_dir / pkg.loan_reference
    result_dir.mkdir(parents=True, exist_ok=True)

    (result_dir / "assessment.json").write_text(generate_json_report(assessment))
    (result_dir / "assessment.md").write_text(generate_markdown_report(assessment))
    save_graph(assessment, result_dir)

    return assessment


def print_summary(assessment: FraudAssessment):
    """Print a concise summary to terminal."""
    pkg = assessment.package
    verdict_icon = {"CLEAN": "✓", "REVIEW": "⚠", "SUSPICIOUS": "✗"}
    icon = verdict_icon.get(assessment.verdict, "?")

    print(f"\nNeo Fraud Detection — {assessment.loan_reference}")
    print("━" * 40)
    print(f"Applicant:  {pkg.applicant_name or 'Unknown'}")
    print(f"Employee:   {pkg.employee_name or 'Unknown'} (ID: {pkg.employee_id or '?'})")
    print(f"Balance:    {pkg.total_balance:,} VND")
    if pkg.salary_transactions:
        for t in pkg.salary_transactions:
            print(f"Salary:     {t.amount:,} VND ({t.description or '—'})")
    print()
    print(f"Risk Score: {assessment.risk_score}/100")
    print(f"Verdict:    {assessment.verdict} {icon}")
    print()

    if assessment.findings:
        print("Findings:")
        for f in assessment.findings:
            print(f"  [{f.severity.upper()}] {f.rule_name}")
            print(f"         {f.description}")
    else:
        print("Findings:   None — all rules passed")


def main():
    parser = argparse.ArgumentParser(description="Neo Fraud Detection Pipeline")
    parser.add_argument("input", help="PDF file or directory (with --batch)")
    parser.add_argument("--output-dir", "-o", default="./results", help="Output directory")
    parser.add_argument("--batch", action="store_true", help="Process all PDFs in directory")
    parser.add_argument("--json-only", action="store_true", help="Output JSON only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show progress")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if args.batch:
        if not input_path.is_dir():
            print(f"Error: {input_path} is not a directory", file=sys.stderr)
            sys.exit(1)
        pdfs = list(input_path.rglob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {input_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Batch processing {len(pdfs)} PDFs...")
        for pdf in pdfs:
            assessment = asyncio.run(process_single(pdf, output_dir, args.verbose))
            print_summary(assessment)
    else:
        if not input_path.is_file():
            print(f"Error: {input_path} is not a file", file=sys.stderr)
            sys.exit(1)
        assessment = asyncio.run(process_single(input_path, output_dir, args.verbose))
        print_summary(assessment)
        print(f"\nSaved: {output_dir / assessment.loan_reference}/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI manually**

```bash
GEMINI_API_KEY=test python -m pipeline.cli --help
```

Expected: help text with usage

- [ ] **Step 3: Commit**

```bash
git add pipeline/cli.py
git commit -m "feat: add CLI entry point with batch mode"
```

---

### Task 10: Web App (FastAPI + Drag & Drop UI)

**Files:**
- Create: `pipeline/server.py`
- Create: `pipeline/templates/index.html`

- [ ] **Step 1: Implement server.py**

```python
"""FastAPI web server — drag & drop PDF fraud detection."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pipeline.extract import extract_package
from pipeline.rules import evaluate_all_rules
from pipeline.score import compute_score
from pipeline.report import generate_json_report, generate_markdown_report
from pipeline.graph import save_graph
from pipeline.vision import GeminiVision, ClaudeVision
from pipeline.models import FraudAssessment

app = FastAPI(title="Neo Fraud Detection", version="0.1.0")

RESULTS_DIR = Path("./web-results")
RESULTS_DIR.mkdir(exist_ok=True)

jobs: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    template = Path(__file__).parent / "templates" / "index.html"
    return template.read_text()


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "processing", "progress": [], "result": None}

    pdf_bytes = await file.read()
    tmp_path = RESULTS_DIR / f"{job_id}.pdf"
    tmp_path.write_bytes(pdf_bytes)

    asyncio.create_task(_process_job(job_id, tmp_path, file.filename))

    return {"job_id": job_id}


async def _process_job(job_id: str, pdf_path: Path, filename: str):
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

        primary = GeminiVision(api_key=gemini_key)
        fallback = ClaudeVision(api_key=anthropic_key) if anthropic_key else None

        def on_progress(msg: str):
            jobs[job_id]["progress"].append(msg)

        pkg = await extract_package(pdf_path, primary, fallback, 0.7, on_progress)
        on_progress("Running fraud rules...")

        findings = evaluate_all_rules(pkg)
        risk_score, verdict = compute_score(findings)

        assessment = FraudAssessment(
            loan_reference=pkg.loan_reference,
            risk_score=risk_score,
            verdict=verdict,
            package=pkg,
            findings=findings,
            extraction_provider="hybrid" if fallback else "gemini",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        result_dir = RESULTS_DIR / job_id
        result_dir.mkdir(exist_ok=True)
        (result_dir / "assessment.json").write_text(generate_json_report(assessment))
        (result_dir / "assessment.md").write_text(generate_markdown_report(assessment))
        save_graph(assessment, result_dir)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["result"] = json.loads(generate_json_report(assessment))
        on_progress("Complete!")

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["progress"].append(f"Error: {str(e)}")


@app.get("/api/status/{job_id}")
async def status_stream(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    async def event_stream() -> AsyncGenerator[str, None]:
        last_idx = 0
        while True:
            job = jobs[job_id]
            progress = job["progress"]
            for msg in progress[last_idx:]:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"
            last_idx = len(progress)

            if job["status"] in ("complete", "error"):
                yield f"data: {json.dumps({'type': 'done', 'status': job['status'], 'result': job.get('result')})}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in jobs or jobs[job_id]["status"] != "complete":
        raise HTTPException(404, "Results not ready")
    return jobs[job_id]["result"]


@app.get("/api/graph/{job_id}")
async def get_graph(job_id: str):
    graph_path = RESULTS_DIR / job_id / "graph.html"
    if not graph_path.exists():
        raise HTTPException(404, "Graph not found")
    return FileResponse(graph_path, media_type="text/html")


def main():
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Neo Fraud Detection</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
.container { max-width: 900px; margin: 0 auto; padding: 2rem; }
h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
h1 span { color: #4ade80; }
.subtitle { color: #888; margin-bottom: 2rem; }

.drop-zone { border: 2px dashed #333; border-radius: 12px; padding: 4rem 2rem; text-align: center; cursor: pointer; transition: all 0.2s; }
.drop-zone:hover, .drop-zone.dragover { border-color: #4ade80; background: rgba(74,222,128,0.05); }
.drop-zone p { font-size: 1.1rem; color: #888; }
.drop-zone input { display: none; }

.progress { display: none; margin: 2rem 0; }
.progress.active { display: block; }
.progress-log { background: #111; border-radius: 8px; padding: 1rem; font-family: monospace; font-size: 0.85rem; max-height: 200px; overflow-y: auto; }
.progress-log div { padding: 2px 0; color: #4ade80; }

.result { display: none; margin: 2rem 0; }
.result.active { display: block; }

.verdict-badge { display: inline-block; padding: 0.5rem 1.5rem; border-radius: 8px; font-size: 1.2rem; font-weight: 700; margin: 1rem 0; }
.verdict-CLEAN { background: #065f46; color: #4ade80; }
.verdict-REVIEW { background: #78350f; color: #fbbf24; }
.verdict-SUSPICIOUS { background: #7f1d1d; color: #f87171; }

.score { font-size: 3rem; font-weight: 700; }
.score-label { color: #888; font-size: 0.9rem; }

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }
.info-card { background: #111; border-radius: 8px; padding: 1rem; }
.info-card label { color: #888; font-size: 0.8rem; display: block; margin-bottom: 0.3rem; }
.info-card span { font-size: 1rem; }

.findings { margin: 1.5rem 0; }
.finding { background: #111; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid; }
.finding.critical { border-color: #f87171; }
.finding.warning { border-color: #fbbf24; }
.finding.info { border-color: #60a5fa; }
.finding .severity { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
.finding .name { font-weight: 600; margin: 0.3rem 0; }
.finding .evidence { color: #888; font-size: 0.85rem; }

.graph-frame { width: 100%; height: 500px; border: 1px solid #222; border-radius: 8px; margin: 1rem 0; }

.actions { display: flex; gap: 1rem; margin: 1rem 0; }
.btn { padding: 0.6rem 1.2rem; border-radius: 6px; border: 1px solid #333; background: #111; color: #e0e0e0; cursor: pointer; font-size: 0.9rem; }
.btn:hover { background: #222; }
.btn-primary { background: #4ade80; color: #000; border: none; font-weight: 600; }
</style>
</head>
<body>
<div class="container">
  <h1><span>Neo</span> Fraud Detection</h1>
  <p class="subtitle">Drop a bank statement PDF — get an instant fraud assessment</p>

  <div class="drop-zone" id="dropZone">
    <p>Drag & drop PDF here, or click to select</p>
    <input type="file" id="fileInput" accept=".pdf">
  </div>

  <div class="progress" id="progress">
    <h3>Processing...</h3>
    <div class="progress-log" id="progressLog"></div>
  </div>

  <div class="result" id="result">
    <div style="display:flex;align-items:center;gap:2rem;">
      <div>
        <div class="score" id="riskScore">0</div>
        <div class="score-label">Risk Score</div>
      </div>
      <div class="verdict-badge" id="verdictBadge">CLEAN</div>
    </div>

    <div class="info-grid">
      <div class="info-card"><label>Applicant</label><span id="applicantName">—</span></div>
      <div class="info-card"><label>Employee</label><span id="employeeName">—</span></div>
      <div class="info-card"><label>Total Balance</label><span id="totalBalance">—</span></div>
      <div class="info-card"><label>Pages Analyzed</label><span id="pagesCount">—</span></div>
    </div>

    <div class="findings" id="findings"></div>

    <h3 style="margin:1.5rem 0 0.5rem">Knowledge Graph</h3>
    <iframe class="graph-frame" id="graphFrame"></iframe>

    <div class="actions">
      <button class="btn" onclick="downloadJSON()">Download JSON</button>
      <button class="btn" onclick="downloadMD()">Download Report</button>
      <button class="btn btn-primary" onclick="resetUI()">Analyze Another</button>
    </div>
  </div>
</div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const progressDiv = document.getElementById('progress');
const progressLog = document.getElementById('progressLog');
const resultDiv = document.getElementById('result');
let currentJobId = null;
let currentResult = null;

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFile(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

async function handleFile(file) {
  if (!file.name.endsWith('.pdf')) { alert('Please upload a PDF file'); return; }
  dropZone.style.display = 'none';
  progressDiv.classList.add('active');
  progressLog.innerHTML = '';

  const form = new FormData();
  form.append('file', file);

  const resp = await fetch('/api/analyze', { method: 'POST', body: form });
  const { job_id } = await resp.json();
  currentJobId = job_id;

  const es = new EventSource(`/api/status/${job_id}`);
  es.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'progress') {
      const div = document.createElement('div');
      div.textContent = data.message;
      progressLog.appendChild(div);
      progressLog.scrollTop = progressLog.scrollHeight;
    } else if (data.type === 'done') {
      es.close();
      if (data.status === 'complete') showResult(data.result);
      else { progressLog.innerHTML += '<div style="color:#f87171">Processing failed</div>'; }
    }
  };
}

function showResult(data) {
  currentResult = data;
  progressDiv.classList.remove('active');
  resultDiv.classList.add('active');

  document.getElementById('riskScore').textContent = data.risk_score;
  const badge = document.getElementById('verdictBadge');
  badge.textContent = data.verdict;
  badge.className = 'verdict-badge verdict-' + data.verdict;

  document.getElementById('applicantName').textContent = data.applicant?.name || '—';
  document.getElementById('employeeName').textContent = (data.employee?.name || '—') + (data.employee?.id ? ` (ID: ${data.employee.id})` : '');
  document.getElementById('totalBalance').textContent = (data.applicant?.total_balance || 0).toLocaleString() + ' VND';
  document.getElementById('pagesCount').textContent = data.pages_analyzed || '—';

  const findingsDiv = document.getElementById('findings');
  findingsDiv.innerHTML = '';
  if (data.findings && data.findings.length > 0) {
    data.findings.forEach(f => {
      findingsDiv.innerHTML += `<div class="finding ${f.severity}"><div class="severity">${f.severity}</div><div class="name">${f.rule_name}</div><div class="evidence">${f.evidence}</div></div>`;
    });
  } else {
    findingsDiv.innerHTML = '<p style="color:#4ade80;padding:1rem">All rules passed — no findings</p>';
  }

  document.getElementById('graphFrame').src = `/api/graph/${currentJobId}`;
}

function downloadJSON() { if (currentResult) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(currentResult, null, 2)])); a.download = `${currentResult.loan_reference}_assessment.json`; a.click(); } }
function downloadMD() { if (currentJobId) window.open(`/api/results/${currentJobId}`); }
function resetUI() { dropZone.style.display = ''; resultDiv.classList.remove('active'); progressDiv.classList.remove('active'); currentJobId = null; currentResult = null; }
</script>
</body>
</html>
```

- [ ] **Step 3: Test server starts**

```bash
python -c "from pipeline.server import app; print('Server module OK')"
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/server.py pipeline/templates/index.html
git commit -m "feat: add FastAPI web app with drag-and-drop UI"
```

---

### Task 11: Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY pipeline/ pipeline/
COPY workspaces/ workspaces/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "pipeline.server"]
```

- [ ] **Step 2: Create .dockerignore**

```
.git
__pycache__
*.pyc
results/
web-results/
bank-statements/
*.pdf
.env
```

- [ ] **Step 3: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "feat: add Dockerfile for deployment"
```

---

### Task 12: Integration Test with Real PDFs

- [ ] **Step 1: Run CLI on real bank statement**

```bash
export GEMINI_API_KEY=<your-key>
export ANTHROPIC_API_KEY=<your-key>
python -m pipeline.cli "bank-statements/MBbank- mobile app/MBBbank- mobile app -mã LN2501104785157.pdf" --verbose
```

Expected: Full assessment output with applicant name, balance, salary, score, verdict.

- [ ] **Step 2: Run batch on both PDFs**

```bash
python -m pipeline.cli "bank-statements/MBbank- mobile app/" --batch --verbose
```

Expected: Two assessments, one per PDF.

- [ ] **Step 3: Start web server and test in browser**

```bash
python -m pipeline.server --port 8000
```

Open `http://localhost:8000`, drag a PDF, verify assessment appears.

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit all results**

```bash
git add -A
git commit -m "feat: complete fraud detection pipeline — CLI, web app, tests passing"
git push
```
