from __future__ import annotations

from pathlib import Path
from typing import Callable
from unittest.mock import AsyncMock, patch

import fitz
import pytest

from pipeline.models import PackageData
from pipeline.vision import GeminiVision, ClaudeVision
from tests.test_vision import SAMPLE_VISION_RESPONSE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf_bytes(num_pages: int = 1) -> bytes:
    """Create a minimal in-memory PDF with the given number of pages."""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=200, height=200)
        page.insert_text((10, 100), f"Page {i + 1}")
    buf = doc.tobytes()
    doc.close()
    return buf


# ---------------------------------------------------------------------------
# split_pdf_to_images
# ---------------------------------------------------------------------------


class TestSplitPdfToImages:
    def test_single_page_returns_one_png(self, tmp_path: Path) -> None:
        from pipeline.extract import split_pdf_to_images

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(1))

        images = split_pdf_to_images(pdf_file)

        assert len(images) == 1
        # PNG magic bytes: \x89PNG
        assert images[0][:4] == b"\x89PNG"

    def test_multiple_pages_returns_correct_count(self, tmp_path: Path) -> None:
        from pipeline.extract import split_pdf_to_images

        pdf_file = tmp_path / "multi.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(5))

        images = split_pdf_to_images(pdf_file)

        assert len(images) == 5

    def test_each_item_is_bytes(self, tmp_path: Path) -> None:
        from pipeline.extract import split_pdf_to_images

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(2))

        images = split_pdf_to_images(pdf_file)

        assert all(isinstance(img, bytes) for img in images)

    def test_custom_dpi_accepted(self, tmp_path: Path) -> None:
        from pipeline.extract import split_pdf_to_images

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(1))

        images_low = split_pdf_to_images(pdf_file, dpi=72)
        images_high = split_pdf_to_images(pdf_file, dpi=300)

        assert len(images_low) == 1
        assert len(images_high) == 1
        # Higher DPI produces a larger image
        assert len(images_high[0]) > len(images_low[0])


# ---------------------------------------------------------------------------
# extract_loan_reference
# ---------------------------------------------------------------------------


class TestExtractLoanReference:
    def test_extracts_ln_from_mbbbank_filename(self) -> None:
        from pipeline.extract import extract_loan_reference

        result = extract_loan_reference("MBBbank- mobile app -mã LN2501104785157.pdf")
        assert result == "LN2501104785157"

    def test_returns_unknown_when_no_ln_present(self) -> None:
        from pipeline.extract import extract_loan_reference

        result = extract_loan_reference("some-file.pdf")
        assert result == "UNKNOWN"

    def test_extracts_ln_at_start_of_filename(self) -> None:
        from pipeline.extract import extract_loan_reference

        result = extract_loan_reference("LN2501134790716.pdf")
        assert result == "LN2501134790716"

    def test_returns_unknown_for_empty_string(self) -> None:
        from pipeline.extract import extract_loan_reference

        result = extract_loan_reference("")
        assert result == "UNKNOWN"

    def test_extracts_first_match_when_multiple(self) -> None:
        from pipeline.extract import extract_loan_reference

        result = extract_loan_reference("LN111-LN222.pdf")
        assert result == "LN111"


# ---------------------------------------------------------------------------
# extract_package
# ---------------------------------------------------------------------------


class TestExtractPackage:
    @pytest.mark.asyncio
    async def test_merges_pages_into_package_data(self, tmp_path: Path) -> None:
        from pipeline.extract import extract_package

        pdf_file = tmp_path / "LN2501104785157.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(2))

        primary = GeminiVision(api_key="test-key")
        fallback = ClaudeVision(api_key="test-key")

        fake_image = b"\x89PNG\r\nfake"

        with (
            patch("pipeline.extract.split_pdf_to_images", return_value=[fake_image, fake_image]),
            patch.object(primary, "_call_api", new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE)),
        ):
            result = await extract_package(pdf_file, primary=primary, fallback=fallback)

        assert isinstance(result, PackageData)
        assert result.loan_reference == "LN2501104785157"
        assert len(result.pages) == 2
        # applicant_name comes from first account's holder_name in SAMPLE_VISION_RESPONSE
        assert result.applicant_name == "TRAN THI BINH"

    @pytest.mark.asyncio
    async def test_loan_reference_unknown_for_plain_filename(self, tmp_path: Path) -> None:
        from pipeline.extract import extract_package

        pdf_file = tmp_path / "no_ln_here.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(1))

        primary = GeminiVision(api_key="test-key")

        fake_image = b"\x89PNG\r\nfake"

        with (
            patch("pipeline.extract.split_pdf_to_images", return_value=[fake_image]),
            patch.object(primary, "_call_api", new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE)),
        ):
            result = await extract_package(pdf_file, primary=primary, fallback=None)

        assert result.loan_reference == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_on_progress_called_per_page(self, tmp_path: Path) -> None:
        from pipeline.extract import extract_package

        pdf_file = tmp_path / "LN123.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(3))

        primary = GeminiVision(api_key="test-key")

        fake_image = b"\x89PNG\r\nfake"
        progress_calls: list[str] = []

        with (
            patch("pipeline.extract.split_pdf_to_images", return_value=[fake_image] * 3),
            patch.object(primary, "_call_api", new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE)),
        ):
            result = await extract_package(
                pdf_file,
                primary=primary,
                fallback=None,
                on_progress=progress_calls.append,
            )

        assert len(progress_calls) == 3

    @pytest.mark.asyncio
    async def test_returns_immutable_package_data(self, tmp_path: Path) -> None:
        from pipeline.extract import extract_package

        pdf_file = tmp_path / "LN999.pdf"
        pdf_file.write_bytes(_make_pdf_bytes(1))

        primary = GeminiVision(api_key="test-key")
        fake_image = b"\x89PNG\r\nfake"

        with (
            patch("pipeline.extract.split_pdf_to_images", return_value=[fake_image]),
            patch.object(primary, "_call_api", new=AsyncMock(return_value=SAMPLE_VISION_RESPONSE)),
        ):
            result = await extract_package(pdf_file, primary=primary, fallback=None)

        # PackageData is frozen — assignment should raise
        with pytest.raises((AttributeError, TypeError)):
            result.loan_reference = "MUTATED"  # type: ignore[misc]
