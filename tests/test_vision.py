from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from pipeline.models import BadgeData, PageData
from pipeline.vision import (
    ClaudeVision,
    GeminiVision,
    extract_with_fallback,
    parse_vision_response,
)

# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------

SAMPLE_VISION_RESPONSE: dict = {
    "page_number": 2,
    "screen_type": "TRANSACTION_HISTORY",
    "confidence": 0.92,
    "badge": {
        "name": "Nguyễn Văn An",
        "employee_id": "77001",
        "visible": True,
        "confidence": 0.95,
    },
    "accounts": [
        {
            "number": "1234567890123",
            "holder_name": "TRAN THI BINH",
            "balance": 5000000,
            "currency": "VND",
            "type": "SAVINGS",
            "is_default": False,
        }
    ],
    "transactions": [
        {
            "amount": 8500000,
            "direction": "CREDIT",
            "counterparty": "CONG TY XYZ",
            "description": "Lương tháng 04/2024",
            "timestamp": "2024-04-25T09:00:00",
            "reference": "TXN20240425",
            "is_salary": True,
        },
        {
            "amount": 200000,
            "direction": "DEBIT",
            "counterparty": None,
            "description": "ATM withdrawal",
            "timestamp": "2024-04-26T14:30:00",
            "reference": None,
            "is_salary": False,
        },
    ],
    "device": {
        "type": "IOS",
        "model": "iPhone 14 Pro",
    },
    "photo_metadata": {
        "timestamp": "2024-04-25T09:05:00",
        "location": "10.7769,106.7009",
        "has_metadata": True,
    },
    "background_document": {
        "type": "CMND",
    },
}


# ---------------------------------------------------------------------------
# parse_vision_response — full response
# ---------------------------------------------------------------------------


class TestParseVisionResponseFull:
    def test_page_number(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.page_number == 2

    def test_screen_type(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.screen_type == "TRANSACTION_HISTORY"

    def test_confidence(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.confidence == pytest.approx(0.92)

    def test_badge_parsed(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.badge is not None
        assert result.badge.name == "Nguyễn Văn An"
        assert result.badge.employee_id == "77001"
        assert result.badge.visible is True
        assert result.badge.confidence == pytest.approx(0.95)

    def test_accounts_parsed(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert len(result.accounts) == 1
        acc = result.accounts[0]
        assert acc.number == "1234567890123"
        assert acc.holder_name == "TRAN THI BINH"
        assert acc.balance == 5000000
        assert acc.currency == "VND"
        assert acc.type == "SAVINGS"
        assert acc.is_default is False

    def test_transactions_parsed(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert len(result.transactions) == 2

    def test_salary_transaction_flagged(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        salary_txns = [t for t in result.transactions if t.is_salary]
        assert len(salary_txns) == 1
        assert salary_txns[0].amount == 8500000

    def test_device_type(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.device_type == "IOS"

    def test_device_model(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.device_model == "iPhone 14 Pro"

    def test_photo_timestamp(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.photo_timestamp == "2024-04-25T09:05:00"

    def test_photo_location(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.photo_location == "10.7769,106.7009"

    def test_has_metadata(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.has_metadata is True

    def test_background_document_type(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert result.background_document_type == "CMND"

    def test_result_is_page_data(self) -> None:
        result = parse_vision_response(SAMPLE_VISION_RESPONSE)
        assert isinstance(result, PageData)


# ---------------------------------------------------------------------------
# parse_vision_response — minimal response (defaults)
# ---------------------------------------------------------------------------


class TestParseVisionResponseMinimal:
    MINIMAL: dict = {
        "page_number": 5,
        "screen_type": "ACCOUNT_OVERVIEW",
        "confidence": 0.55,
    }

    def test_page_number_preserved(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.page_number == 5

    def test_screen_type_preserved(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.screen_type == "ACCOUNT_OVERVIEW"

    def test_confidence_preserved(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.confidence == pytest.approx(0.55)

    def test_badge_defaults_to_none(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.badge is None

    def test_accounts_defaults_to_empty(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.accounts == []

    def test_transactions_defaults_to_empty(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.transactions == []

    def test_device_type_defaults_to_none(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.device_type is None

    def test_device_model_defaults_to_none(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.device_model is None

    def test_photo_timestamp_defaults_to_none(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.photo_timestamp is None

    def test_has_metadata_defaults_to_false(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.has_metadata is False

    def test_background_document_type_defaults_to_none(self) -> None:
        result = parse_vision_response(self.MINIMAL)
        assert result.background_document_type is None


# ---------------------------------------------------------------------------
# parse_vision_response — empty dict
# ---------------------------------------------------------------------------


class TestParseVisionResponseEmpty:
    def test_page_number_is_zero(self) -> None:
        result = parse_vision_response({})
        assert result.page_number == 0

    def test_confidence_is_zero(self) -> None:
        result = parse_vision_response({})
        assert result.confidence == pytest.approx(0.0)

    def test_screen_type_has_default(self) -> None:
        result = parse_vision_response({})
        assert isinstance(result.screen_type, str)

    def test_accounts_empty(self) -> None:
        result = parse_vision_response({})
        assert result.accounts == []

    def test_transactions_empty(self) -> None:
        result = parse_vision_response({})
        assert result.transactions == []


# ---------------------------------------------------------------------------
# GeminiVision.extract_page
# ---------------------------------------------------------------------------


class TestGeminiVisionExtractPage:
    @pytest.mark.asyncio
    async def test_calls_api_and_returns_page_data(self) -> None:
        vision = GeminiVision(api_key="test-key")
        with patch.object(
            vision,
            "_call_api",
            new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE),
        ) as mock_call:
            result = await vision.extract_page(b"fake-image-bytes", page_number=2)

        mock_call.assert_awaited_once_with(b"fake-image-bytes", 2)
        assert isinstance(result, PageData)
        assert result.page_number == 2
        assert result.confidence == pytest.approx(0.92)

    @pytest.mark.asyncio
    async def test_passes_page_number_to_api(self) -> None:
        vision = GeminiVision(api_key="test-key")
        with patch.object(
            vision,
            "_call_api",
            new=AsyncMock(return_value={"page_number": 7, "screen_type": "X", "confidence": 0.8}),
        ) as mock_call:
            await vision.extract_page(b"img", page_number=7)

        _, call_page = mock_call.call_args[0]
        assert call_page == 7


# ---------------------------------------------------------------------------
# ClaudeVision.extract_page
# ---------------------------------------------------------------------------


class TestClaudeVisionExtractPage:
    @pytest.mark.asyncio
    async def test_calls_api_and_returns_page_data(self) -> None:
        vision = ClaudeVision(api_key="test-key")
        with patch.object(
            vision,
            "_call_api",
            new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE),
        ) as mock_call:
            result = await vision.extract_page(b"fake-image-bytes", page_number=2)

        mock_call.assert_awaited_once_with(b"fake-image-bytes", 2)
        assert isinstance(result, PageData)
        assert result.page_number == 2

    @pytest.mark.asyncio
    async def test_passes_page_number_to_api(self) -> None:
        vision = ClaudeVision(api_key="test-key")
        with patch.object(
            vision,
            "_call_api",
            new=AsyncMock(return_value={"page_number": 3, "screen_type": "Y", "confidence": 0.75}),
        ) as mock_call:
            await vision.extract_page(b"img", page_number=3)

        _, call_page = mock_call.call_args[0]
        assert call_page == 3


# ---------------------------------------------------------------------------
# extract_with_fallback
# ---------------------------------------------------------------------------


class TestExtractWithFallback:
    def _make_page(self, confidence: float, page_number: int = 1) -> PageData:
        return PageData(
            page_number=page_number,
            screen_type="BANK_STATEMENT",
            confidence=confidence,
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

    @pytest.mark.asyncio
    async def test_high_confidence_skips_fallback(self) -> None:
        primary = GeminiVision(api_key="g-key")
        fallback = ClaudeVision(api_key="c-key")
        high_conf_page = self._make_page(confidence=0.9)

        with (
            patch.object(primary, "extract_page", new=AsyncMock(return_value=high_conf_page)),
            patch.object(fallback, "extract_page", new=AsyncMock()) as mock_fallback,
        ):
            result = await extract_with_fallback(
                b"img", 1, primary=primary, fallback=fallback, threshold=0.7
            )

        mock_fallback.assert_not_awaited()
        assert result.confidence == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_fallback_returns_better(self) -> None:
        primary = GeminiVision(api_key="g-key")
        fallback = ClaudeVision(api_key="c-key")
        low_conf_page = self._make_page(confidence=0.5)
        high_conf_page = self._make_page(confidence=0.88)

        with (
            patch.object(primary, "extract_page", new=AsyncMock(return_value=low_conf_page)),
            patch.object(fallback, "extract_page", new=AsyncMock(return_value=high_conf_page)) as mock_fallback,
        ):
            result = await extract_with_fallback(
                b"img", 1, primary=primary, fallback=fallback, threshold=0.7
            )

        mock_fallback.assert_awaited_once()
        assert result.confidence == pytest.approx(0.88)

    @pytest.mark.asyncio
    async def test_low_confidence_returns_primary_when_fallback_worse(self) -> None:
        primary = GeminiVision(api_key="g-key")
        fallback = ClaudeVision(api_key="c-key")
        low_conf_primary = self._make_page(confidence=0.5)
        even_lower_fallback = self._make_page(confidence=0.3)

        with (
            patch.object(primary, "extract_page", new=AsyncMock(return_value=low_conf_primary)),
            patch.object(fallback, "extract_page", new=AsyncMock(return_value=even_lower_fallback)),
        ):
            result = await extract_with_fallback(
                b"img", 1, primary=primary, fallback=fallback, threshold=0.7
            )

        assert result.confidence == pytest.approx(0.5)

    @pytest.mark.asyncio
    async def test_fallback_none_returns_primary_even_if_low_confidence(self) -> None:
        primary = GeminiVision(api_key="g-key")
        low_conf_page = self._make_page(confidence=0.3)

        with patch.object(primary, "extract_page", new=AsyncMock(return_value=low_conf_page)):
            result = await extract_with_fallback(
                b"img", 1, primary=primary, fallback=None, threshold=0.7
            )

        assert result.confidence == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_fallback_none_type_annotation_accepted(self) -> None:
        """Passing fallback=None should not raise any errors."""
        primary = GeminiVision(api_key="g-key")
        page = self._make_page(confidence=0.95)

        with patch.object(primary, "extract_page", new=AsyncMock(return_value=page)):
            result = await extract_with_fallback(b"img", 1, primary=primary, fallback=None)

        assert isinstance(result, PageData)
