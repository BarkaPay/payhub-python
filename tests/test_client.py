from __future__ import annotations

import json

from payhub import PayHub, Payment, PaymentStatus
from tests.support import FakeTransport, json_response


def test_create_payment_builds_signed_country_scoped_request() -> None:
    http = FakeTransport(
        [
            json_response(
                201,
                {
                    "status": "success",
                    "code": "resource_created",
                    "data": {
                        "payment": {
                            "public_id": "pay_1",
                            "status": "SUCCESSFUL",
                            "amount": 10000,
                            "currency": "XOF",
                        }
                    },
                },
            )
        ]
    )

    client = PayHub(api_key="pk_live_x:sk_live_y", country="bf", max_retries=0, transport=http)

    payment = client.payments.create(
        {
            "operator": "ORANGE",
            "phone_number": "50123456789",
            "amount": 10000,
            "order": {"id": "O1"},
        }
    )

    assert isinstance(payment, Payment)
    assert payment.public_id == "pay_1"
    assert payment.status is PaymentStatus.SUCCESSFUL

    request = http.last_request
    assert request is not None
    assert request.method == "POST"
    assert request.url == "https://hub.barkapay.com/bf/v1/payments"
    assert request.headers["Authorization"] == "Bearer pk_live_x:sk_live_y"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-Agent"].startswith("payhub-python/")
    assert "X-Request-Id" in request.headers

    assert request.body is not None
    body = json.loads(request.body)
    assert body["operator"] == "ORANGE"


def test_country_can_be_overridden_per_call() -> None:
    http = FakeTransport([json_response(200, {"status": "success", "data": {}})])
    client = PayHub(api_key="k:s", country="bf", max_retries=0, transport=http)

    client.ping("sn")

    assert http.last_request is not None
    assert http.last_request.url == "https://hub.barkapay.com/sn/v1/ping"


def test_keyid_secret_pair_builds_authorization() -> None:
    http = FakeTransport([json_response(200, {"status": "success", "data": {}})])
    client = PayHub(key_id="k", secret="s", country="bf", max_retries=0, transport=http)

    client.ping()

    assert http.last_request is not None
    assert http.last_request.headers["Authorization"] == "Bearer k:s"


def test_accidental_bearer_prefix_is_forgiven() -> None:
    http = FakeTransport([json_response(200, {"status": "success", "data": {}})])
    client = PayHub(api_key="Bearer k:s", country="bf", max_retries=0, transport=http)

    client.ping()

    assert http.last_request is not None
    assert http.last_request.headers["Authorization"] == "Bearer k:s"


def test_list_hydrates_collection_pagination_and_query_string() -> None:
    http = FakeTransport(
        [
            json_response(
                200,
                {
                    "status": "success",
                    "data": {
                        "payments": [
                            {"public_id": "p1", "status": "SUCCESSFUL"},
                            {"public_id": "p2", "status": "FAILED"},
                        ]
                    },
                    "meta": {
                        "current_page": 1,
                        "last_page": 1,
                        "per_page": 50,
                        "total": 2,
                    },
                },
            )
        ]
    )
    client = PayHub(api_key="k:s", country="bf", max_retries=0, transport=http)

    listing = client.payments.list({"status": "SUCCESSFUL"})

    assert len(listing) == 2
    assert listing.meta is not None
    assert listing.meta.total == 2
    assert [p.public_id for p in listing] == ["p1", "p2"]
    assert http.last_request is not None
    assert "status=SUCCESSFUL" in http.last_request.url


def test_get_payment_returns_first_row() -> None:
    http = FakeTransport(
        [
            json_response(
                200,
                {"status": "success", "data": {"payments": [{"public_id": "pay_42"}]}},
            )
        ]
    )
    client = PayHub(api_key="k:s", country="bf", max_retries=0, transport=http)

    payment = client.payments.get("pay_42")

    assert payment.public_id == "pay_42"
    assert http.last_request is not None
    assert http.last_request.url == "https://hub.barkapay.com/bf/v1/payments/pay_42"


def test_confirm_otp_posts_otp_body() -> None:
    http = FakeTransport(
        [
            json_response(
                200,
                {"status": "success", "data": {"payment": {"public_id": "pay_1"}}},
            )
        ]
    )
    client = PayHub(api_key="k:s", country="bf", max_retries=0, transport=http)

    client.payments.confirm_otp("pay_1", "123456")

    req = http.last_request
    assert req is not None
    assert req.url == "https://hub.barkapay.com/bf/v1/payments/pay_1/confirm-otp"
    assert req.body is not None
    assert json.loads(req.body) == {"otp": "123456"}


def test_balance_get() -> None:
    http = FakeTransport(
        [
            json_response(
                200,
                {
                    "status": "success",
                    "data": {
                        "country": "BF",
                        "currency": "XOF",
                        "available": "1500.00",
                        "total": "1500.00",
                        "holds": "0.00",
                    },
                },
            )
        ]
    )
    client = PayHub(api_key="k:s", country="bf", max_retries=0, transport=http)

    balance = client.balance.get()

    assert balance.available == "1500.00"
    assert balance.currency == "XOF"
    assert http.last_request is not None
    assert http.last_request.url == "https://hub.barkapay.com/bf/v1/balance"


def test_retries_on_503_then_succeeds() -> None:
    http = FakeTransport(
        [
            json_response(
                503,
                {"status": "error", "code": "service_unavailable", "message": "down"},
            ),
            json_response(200, {"status": "success", "data": {}}),
        ]
    )
    client = PayHub(api_key="k:s", country="bf", max_retries=1, transport=http)

    client.ping()

    assert len(http.requests) == 2


def test_missing_country_raises_configuration_error() -> None:
    from payhub import ConfigurationError

    http = FakeTransport([json_response(200, {"status": "success", "data": {}})])
    client = PayHub(api_key="k:s", max_retries=0, transport=http)

    try:
        client.ping()
        raise AssertionError("expected ConfigurationError")
    except ConfigurationError:
        pass


def test_missing_credentials_raises_configuration_error() -> None:
    from payhub import ConfigurationError

    try:
        PayHub(country="bf")
        raise AssertionError("expected ConfigurationError")
    except ConfigurationError:
        pass
