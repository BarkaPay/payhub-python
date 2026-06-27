from __future__ import annotations

import pytest

from payhub import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    PayHub,
    RateLimitError,
    ValidationError,
)
from payhub.http import Response
from tests.support import FakeTransport, json_response


def _client(response: Response, max_retries: int = 0) -> PayHub:
    return PayHub(
        api_key="k:s",
        country="bf",
        max_retries=max_retries,
        transport=FakeTransport([response]),
    )


def test_validation_error_maps_and_exposes_fields() -> None:
    client = _client(
        json_response(
            422,
            {
                "status": "failed",
                "code": "validation_error",
                "message": "The given data was invalid.",
                "request_id": "rid-1",
                "errors": {"operator": ["Unknown operator."]},
            },
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        client.payments.create({"x": 1})

    err = exc_info.value
    assert err.code == "validation_error"
    assert err.http_status == 422
    assert err.request_id == "rid-1"
    assert err.errors == {"operator": ["Unknown operator."]}


def test_authentication_error() -> None:
    client = _client(
        json_response(
            401,
            {"status": "failed", "code": "invalid_api_key", "message": "bad key"},
        )
    )
    with pytest.raises(AuthenticationError):
        client.me()


def test_conflict_error() -> None:
    client = _client(
        json_response(
            409,
            {"status": "failed", "code": "duplicate_transaction", "message": "dup"},
        )
    )
    with pytest.raises(ConflictError):
        client.transfers.create({"x": 1})


def test_rate_limit_error_after_retries_exhausted() -> None:
    client = _client(
        json_response(
            429,
            {"status": "error", "code": "too_many_requests", "message": "slow down"},
        ),
        max_retries=0,
    )
    with pytest.raises(RateLimitError):
        client.balance.get()


def test_request_id_falls_back_to_generated_when_absent() -> None:
    client = _client(
        json_response(500, {"status": "error", "code": "server_error", "message": "boom"})
    )
    from payhub import ServerError

    with pytest.raises(ServerError) as exc_info:
        client.ping()
    assert exc_info.value.request_id is not None


def test_network_error_bubbles_up() -> None:
    client = PayHub(
        api_key="k:s",
        country="bf",
        max_retries=0,
        transport=FakeTransport([NetworkError("connection refused")]),
    )
    with pytest.raises(NetworkError):
        client.ping()
