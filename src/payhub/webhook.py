"""Verify the ``PayHub-Signature`` header on incoming webhooks.

The header is ``t=<unix_ts>,v1=<hex>`` where ``v1 = HMAC-SHA256("{t}.{rawBody}")``
keyed with your endpoint secret (``whsec_…``). Always verify against the RAW
request body — not a re-encoded copy.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Union

from ._util import json_decode
from .errors import SignatureVerificationError

DEFAULT_TOLERANCE = 300

_Payload = Union[str, bytes]

__all__ = ["DEFAULT_TOLERANCE", "parse", "verify"]


def verify(
    payload: _Payload,
    signature_header: str,
    secret: str,
    tolerance: int = DEFAULT_TOLERANCE,
) -> bool:
    """Return ``True`` if the signature is valid, ``False`` otherwise.

    :param payload: the raw request body (``str`` or ``bytes``).
    :param signature_header: the ``PayHub-Signature`` header value.
    :param secret: your endpoint signing secret (``whsec_…``).
    :param tolerance: max clock skew in seconds (0 disables the check).
    """
    try:
        _assert(payload, signature_header, secret, tolerance)
        return True
    except SignatureVerificationError:
        return False


def parse(
    payload: _Payload,
    signature_header: str,
    secret: str,
    tolerance: int = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Verify and decode the webhook body in one step.

    :raises SignatureVerificationError: if the signature is invalid or the body
        is not a JSON object.
    """
    _assert(payload, signature_header, secret, tolerance)

    data = json_decode(payload)
    if data is None:
        raise SignatureVerificationError("Webhook payload is not valid JSON.")
    return data


def _assert(payload: _Payload, header: str, secret: str, tolerance: int) -> None:
    parsed = _parse_header(header)
    if parsed is None:
        raise SignatureVerificationError("Malformed or missing PayHub-Signature header.")

    timestamp, signature = parsed

    if tolerance > 0 and abs(int(time.time()) - timestamp) > tolerance:
        raise SignatureVerificationError("Webhook timestamp is outside the tolerance window.")

    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    message = f"{timestamp}.".encode() + raw
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise SignatureVerificationError("Webhook signature mismatch.")


def _parse_header(header: str) -> tuple[int, str] | None:
    timestamp: str | None = None
    signature: str | None = None

    for part in header.split(","):
        pair = part.strip().split("=", 1)
        if len(pair) != 2:
            continue
        key, value = pair
        if key == "t":
            timestamp = value
        elif key == "v1":
            signature = value

    if timestamp is None or signature is None or not timestamp.isdigit():
        return None

    return int(timestamp), signature
