from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

import fitz

from pipeline.models import PackageData, PageData
from pipeline.vision import ClaudeVision, GeminiVision, extract_with_fallback

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LN_PATTERN = re.compile(r"(LN\d+)")

# ---------------------------------------------------------------------------
# split_pdf_to_images
# ---------------------------------------------------------------------------


def split_pdf_to_images(pdf_path: Path, dpi: int = 200) -> list[bytes]:
    """Render each page of a PDF as PNG bytes and return the list.

    Args:
        pdf_path: Path to the PDF file.
        dpi: Resolution in dots per inch (default 200).

    Returns:
        A list of PNG-encoded bytes, one per page.
    """
    doc = fitz.open(str(pdf_path))
    images: list[bytes] = []
    scale = dpi / 72
    mat = fitz.Matrix(scale, scale)
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


# ---------------------------------------------------------------------------
# extract_loan_reference
# ---------------------------------------------------------------------------


def extract_loan_reference(filename: str) -> str:
    """Extract the loan reference (LN followed by digits) from a filename.

    Args:
        filename: The filename string to search.

    Returns:
        The matched loan reference string (e.g. "LN2501104785157"),
        or "UNKNOWN" if no match is found.
    """
    match = _LN_PATTERN.search(filename)
    if match:
        return match.group(1)
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# extract_package
# ---------------------------------------------------------------------------


async def extract_package(
    pdf_path: Path,
    primary: GeminiVision | ClaudeVision,
    fallback: GeminiVision | ClaudeVision | None,
    confidence_threshold: float = 0.7,
    on_progress: Optional[Callable[[str], None]] = None,
) -> PackageData:
    """Extract structured PackageData from a PDF file.

    Steps:
    1. Split the PDF into per-page PNG images.
    2. Run vision extraction on each page (with fallback if needed).
    3. Optionally call on_progress with a status string per page.
    4. Extract the loan reference from the filename.
    5. Return PackageData.from_pages(loan_reference, pages).

    Args:
        pdf_path: Path to the input PDF.
        primary: Primary vision extractor (GeminiVision).
        fallback: Optional fallback vision extractor (ClaudeVision).
        confidence_threshold: Minimum confidence to skip fallback (default 0.7).
        on_progress: Optional callback invoked with a status string after each page.

    Returns:
        A frozen PackageData aggregated from all pages.
    """
    images = split_pdf_to_images(pdf_path)
    loan_reference = extract_loan_reference(pdf_path.name)

    pages: list[PageData] = []
    for index, image_bytes in enumerate(images):
        page_number = index + 1
        page = await extract_with_fallback(
            image_bytes=image_bytes,
            page_number=page_number,
            primary=primary,
            fallback=fallback,
            threshold=confidence_threshold,
        )
        pages.append(page)
        if on_progress is not None:
            on_progress(f"page {page_number}/{len(images)}: {page.screen_type} (confidence={page.confidence:.2f})")

    return PackageData.from_pages(loan_reference, pages)
