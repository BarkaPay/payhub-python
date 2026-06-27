from __future__ import annotations

import hashlib
import hmac
import time

import pytest

from payhub import SignatureVerificationError, webhook

SECRET = "whsec_test_secret"
PAYLOAD = '{"type":"payment","public_id":"pay_1","status":"SUCCESSFUL"}'


def _sign(payload: str, timestamp: int, secret: str = SECRET) -> str:
    message = f"{timestamp}.{payload}".encode()
    sig = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def test_verify_and_parse_valid_signature() -> None:
    header = _sign(PAYLOAD, int(time.time()))

    assert webhook.verify(PAYLOAD, header, SECRET) is True

    event = webhook.parse(PAYLOAD, header, SECRET)
    assert event["type"] == "payment"
    assert event["status"] == "SUCCESSFUL"


def test_verify_accepts_bytes_payload() -> None:
    header = _sign(PAYLOAD, int(time.time()))
    assert webhook.verify(PAYLOAD.encode(), header, SECRET) is True


def test_rejects_tampered_payload() -> None:
    header = _sign(PAYLOAD, int(time.time()))
    assert webhook.verify('{"type":"payment","amount":"999"}', header, SECRET) is False


def test_rejects_wrong_secret() -> None:
    header = _sign(PAYLOAD, int(time.time()))
    assert webhook.verify(PAYLOAD, header, "whsec_other") is False


def test_rejects_stale_timestamp() -> None:
    header = _sign(PAYLOAD, int(time.time()) - 1000)
    assert webhook.verify(PAYLOAD, header, SECRET) is False


def test_tolerance_zero_disables_timestamp_check() -> None:
    header = _sign(PAYLOAD, int(time.time()) - 100_000)
    assert webhook.verify(PAYLOAD, header, SECRET, tolerance=0) is True


def test_rejects_malformed_header() -> None:
    assert webhook.verify(PAYLOAD, "not-a-signature", SECRET) is False


def test_parse_throws_on_bad_signature() -> None:
    header = _sign(PAYLOAD, int(time.time()))
    with pytest.raises(SignatureVerificationError):
        webhook.parse(PAYLOAD, header, "whsec_other")


def test_parse_throws_on_non_json_object() -> None:
    payload = "[1, 2, 3]"
    header = _sign(payload, int(time.time()))
    with pytest.raises(SignatureVerificationError):
        webhook.parse(payload, header, SECRET)
