"""Internal helpers: defensive readers for decoded JSON and JSON (de)coding.

These keep model hydration null-safe and tidy. Not part of the public API.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any


def as_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    return value if isinstance(value, str) else None


def as_int(data: Mapping[str, Any], key: str) -> int | None:
    value = data.get(key)
    # ``bool`` is a subclass of ``int`` — exclude it to mirror PHP's is_int().
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def as_amount(data: Mapping[str, Any], key: str) -> int | float | str | None:
    """Amount as returned by the API (whole number for fiat, decimal string for
    crypto). Returned as-is to avoid lossy coercion."""
    value = data.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, str)):
        return value
    return None


def as_dict(data: Mapping[str, Any], key: str) -> dict[str, Any] | None:
    value = data.get(key)
    return value if isinstance(value, dict) else None


def as_list_of_dict(data: Mapping[str, Any], key: str) -> list[dict[str, Any]] | None:
    value = data.get(key)
    if not isinstance(value, list):
        return None
    return [item for item in value if isinstance(item, dict)]


def json_encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_decode(payload: str | bytes) -> dict[str, Any] | None:
    """Decode a JSON object into a dict. Returns ``None`` for empty input or
    anything that isn't a JSON object."""
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="replace")
    if payload.strip() == "":
        return None
    try:
        decoded = json.loads(payload)
    except (ValueError, TypeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def generate_request_id() -> str:
    """RFC-4122 v4 UUID, used as the ``X-Request-Id`` correlation id."""
    return str(uuid.uuid4())
