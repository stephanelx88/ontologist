from __future__ import annotations

import base64
import json
import re
from typing import Optional

import anthropic
import google.genai as genai
from google.genai import types as genai_types

from pipeline.models import AccountData, BadgeData, PageData, TransactionData

# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """You are analyzing a photo of a Vietnamese mobile banking app screenshot (VPBank) that may also contain a VPBank employee badge.

Extract all visible data and return ONLY a valid JSON object — no markdown, no explanation, no code fences.

Replace PAGE_NUM with the actual page number you are analyzing.

Required JSON structure:
{
  "page_number": PAGE_NUM,
  "screen_type": "<BANK_STATEMENT | TRANSACTION_HISTORY | ACCOUNT_OVERVIEW | LOGIN | UNKNOWN>",
  "confidence": <0.0–1.0 overall extraction confidence>,
  "badge": {
    "name": "<full name on badge or null>",
    "employee_id": "<employee ID or null>",
    "visible": <true|false>,
    "confidence": <0.0–1.0>
  },
  "accounts": [
    {
      "number": "<account number>",
      "holder_name": "<account holder or null>",
      "balance": <integer VND>,
      "currency": "VND",
      "type": "<CHECKING | SAVINGS | UNKNOWN>",
      "is_default": <true|false>
    }
  ],
  "transactions": [
    {
      "amount": <integer VND>,
      "direction": "<CREDIT | DEBIT>",
      "counterparty": "<name or null>",
      "description": "<description text or null>",
      "timestamp": "<ISO 8601 or null>",
      "reference": "<reference code or null>",
      "is_salary": <true if description contains "lương", "luong", "Luong", or "salary", else false>
    }
  ],
  "device": {
    "type": "<IOS | ANDROID | UNKNOWN or null>",
    "model": "<device model or null>"
  },
  "photo_metadata": {
    "timestamp": "<ISO 8601 or null>",
    "location": "<lat,lon or null>",
    "has_metadata": <true|false>
  },
  "background_document": {
    "type": "<CMND | CCCD | PASSPORT | null>"
  }
}

Rules:
- Preserve Vietnamese diacritics exactly (e.g. "Nguyễn Thị Hằng", "Lương tháng").
- All monetary amounts must be integers in VND (remove dots/commas used as thousand separators).
- Set is_salary=true if and only if the transaction description contains any of: "lương", "luong", "Luong", "salary" (case-sensitive match on "luong"/"Luong"; case-insensitive acceptable for "salary").
- Use null rather than guessing when text is blurry or not visible.
- Return only the JSON object — no surrounding text.
"""

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from a string."""
    match = _FENCE_RE.search(text)
    if match:
        return match.group(1)
    return text.strip()


def _parse_badge(raw: dict | None) -> Optional[BadgeData]:
    if not raw or not isinstance(raw, dict):
        return None
    return BadgeData(
        name=raw.get("name"),
        employee_id=raw.get("employee_id"),
        visible=bool(raw.get("visible", False)),
        confidence=float(raw.get("confidence", 0.0)),
    )


def _parse_account(raw: dict) -> AccountData:
    return AccountData(
        number=str(raw.get("number", "")),
        holder_name=raw.get("holder_name"),
        balance=int(raw.get("balance", 0)),
        currency=str(raw.get("currency", "VND")),
        type=str(raw.get("type", "UNKNOWN")),
        is_default=bool(raw.get("is_default", False)),
    )


def _parse_transaction(raw: dict) -> TransactionData:
    return TransactionData(
        amount=int(raw.get("amount", 0)),
        direction=str(raw.get("direction", "UNKNOWN")),
        counterparty=raw.get("counterparty"),
        description=raw.get("description"),
        timestamp=raw.get("timestamp"),
        reference=raw.get("reference"),
        is_salary=bool(raw.get("is_salary", False)),
    )


# ---------------------------------------------------------------------------
# Public parser
# ---------------------------------------------------------------------------


def parse_vision_response(data: dict) -> PageData:
    """Parse a raw vision API response dict into a PageData model.

    Handles missing fields gracefully — defaults to None / empty list / 0.0.
    An empty dict produces page_number=0, confidence=0.0.
    """
    badge = _parse_badge(data.get("badge"))

    raw_accounts = data.get("accounts") or []
    accounts = [_parse_account(a) for a in raw_accounts if isinstance(a, dict)]

    raw_transactions = data.get("transactions") or []
    transactions = [_parse_transaction(t) for t in raw_transactions if isinstance(t, dict)]

    device = data.get("device") or {}
    photo_meta = data.get("photo_metadata") or {}
    bg_doc = data.get("background_document") or {}

    return PageData(
        page_number=int(data.get("page_number", 0)),
        screen_type=str(data.get("screen_type", "UNKNOWN")),
        confidence=float(data.get("confidence", 0.0)),
        badge=badge,
        accounts=accounts,
        transactions=transactions,
        device_type=device.get("type") if isinstance(device, dict) else None,
        device_model=device.get("model") if isinstance(device, dict) else None,
        photo_timestamp=photo_meta.get("timestamp") if isinstance(photo_meta, dict) else None,
        photo_location=photo_meta.get("location") if isinstance(photo_meta, dict) else None,
        has_metadata=bool(photo_meta.get("has_metadata", False)) if isinstance(photo_meta, dict) else False,
        background_document_type=bg_doc.get("type") if isinstance(bg_doc, dict) else None,
    )


# ---------------------------------------------------------------------------
# GeminiVision
# ---------------------------------------------------------------------------


class GeminiVision:
    """Vision extractor backed by Google Gemini."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self._api_key = api_key
        self._model = model

    async def _call_api(self, image_bytes: bytes, page_number: int) -> dict:
        """Send image + prompt to Gemini and return parsed JSON dict."""
        client = genai.Client(api_key=self._api_key)
        prompt = EXTRACTION_PROMPT.replace("PAGE_NUM", str(page_number))
        image_part = genai_types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        response = client.models.generate_content(
            model=self._model,
            contents=[image_part, prompt],
        )
        raw_text = response.text or ""
        cleaned = _strip_fences(raw_text)
        return json.loads(cleaned)

    async def extract_page(self, image_bytes: bytes, page_number: int) -> PageData:
        """Extract structured data from a single page image."""
        data = await self._call_api(image_bytes, page_number)
        return parse_vision_response(data)


# ---------------------------------------------------------------------------
# ClaudeVision
# ---------------------------------------------------------------------------


class ClaudeVision:
    """Vision extractor backed by Anthropic Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._api_key = api_key
        self._model = model

    async def _call_api(self, image_bytes: bytes, page_number: int) -> dict:
        """Send image + prompt to Claude and return parsed JSON dict."""
        client = anthropic.Anthropic(api_key=self._api_key)
        prompt = EXTRACTION_PROMPT.replace("PAGE_NUM", str(page_number))
        b64_image = base64.standard_b64encode(image_bytes).decode("utf-8")
        message = client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        raw_text = message.content[0].text if message.content else ""
        cleaned = _strip_fences(raw_text)
        return json.loads(cleaned)

    async def extract_page(self, image_bytes: bytes, page_number: int) -> PageData:
        """Extract structured data from a single page image."""
        data = await self._call_api(image_bytes, page_number)
        return parse_vision_response(data)


# ---------------------------------------------------------------------------
# Fallback orchestration
# ---------------------------------------------------------------------------


async def extract_with_fallback(
    image_bytes: bytes,
    page_number: int,
    primary: GeminiVision,
    fallback: ClaudeVision | None,
    threshold: float = 0.7,
) -> PageData:
    """Try primary provider; use fallback if confidence is below threshold.

    Returns whichever result has the higher confidence score.
    If fallback is None, always returns the primary result regardless of confidence.
    """
    primary_result = await primary.extract_page(image_bytes, page_number)

    if fallback is None or primary_result.confidence >= threshold:
        return primary_result

    fallback_result = await fallback.extract_page(image_bytes, page_number)
    return fallback_result if fallback_result.confidence > primary_result.confidence else primary_result
