"""Entry point to the PayHub API."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, urlencode

from ._util import (
    as_dict,
    generate_request_id,
    json_decode,
    json_encode,
)
from ._version import __version__
from .errors import ApiError, ConfigurationError, NetworkError
from .http import Request, Response, Transport, UrllibTransport
from .resources import BalanceResource, Operators, Payments, Transfers

__all__ = ["PayHub"]

_DEFAULT_BASE_URL = "https://hub.barkapay.com"
_BASE_DELAY_S = 0.3
_RETRY_STATUSES = frozenset({429, 503})


class PayHub:
    """Entry point to the PayHub API.

    Example::

        client = PayHub(api_key="pk_live_xxx:sk_live_yyy", country="bf")
        payment = client.payments.create({
            "operator": "ORANGE",
            "phone_number": "50123456789",
            "amount": 10000,
            "otp": "123456",
            "order": {"id": "ORDER-2026-001"},
        })
    """

    VERSION = __version__

    def __init__(
        self,
        api_key: str | None = None,
        *,
        key_id: str | None = None,
        secret: str | None = None,
        country: str = "",
        base_url: str = _DEFAULT_BASE_URL,
        max_retries: int = 2,
        timeout: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        """
        :param api_key: the merchant key as ``"key_id:secret"`` (what you copy
            from the dashboard). Do NOT prefix it with ``Bearer`` — the SDK does that.
        :param key_id: alternatively, the key id…
        :param secret: …and the secret, passed separately.
        :param country: default country code (e.g. ``"bf"``); overridable per call.
        :param base_url: API base URL.
        :param max_retries: automatic retries on 429/503/network errors.
        :param timeout: per-request timeout in seconds.
        :param transport: a custom :class:`~payhub.http.Transport` (e.g. a fake in tests).
        """
        self._api = _ApiClient(
            transport=transport if transport is not None else UrllibTransport(timeout),
            authorization=_build_authorization(api_key, key_id, secret),
            base_url=base_url.rstrip("/"),
            default_country=country.strip().lower(),
            max_retries=max(0, max_retries),
            user_agent=f"payhub-python/{__version__}",
        )

        self.payments = Payments(self._api)
        self.transfers = Transfers(self._api)
        self.balance = BalanceResource(self._api)
        self.operators = Operators(self._api)

    def ping(self, country: str | None = None) -> dict[str, Any]:
        """Liveness check (also confirms your key works)."""
        env = self._api.request("GET", "ping", country=country)
        return as_dict(env, "data") or {}

    def me(self, country: str | None = None) -> dict[str, Any]:
        """Current merchant + API application details."""
        env = self._api.request("GET", "me", country=country)
        return as_dict(env, "data") or {}


def _build_authorization(
    api_key: str | None,
    key_id: str | None,
    secret: str | None,
) -> str:
    if api_key is not None and api_key.strip() != "":
        token = api_key.strip()
        # Forgive an accidental "Bearer " prefix so we never send "Bearer Bearer …".
        if token[:7].lower() == "bearer ":
            token = token[7:].strip()
        return f"Bearer {token}"

    if key_id and secret and key_id.strip() != "" and secret.strip() != "":
        return f"Bearer {key_id.strip()}:{secret.strip()}"

    raise ConfigurationError(
        'Provide `api_key` ("key_id:secret") or both `key_id` and `secret`.'
    )


class _ApiClient:
    """Internal transport: turns a logical call (method, path, country, body)
    into a signed HTTP request against ``{base_url}/{country}/v1/…``, retries
    transient failures, and unwraps the standard response envelope (raising a
    typed :class:`ApiError` on error).
    """

    def __init__(
        self,
        transport: Transport,
        authorization: str,
        base_url: str,
        default_country: str,
        max_retries: int,
        user_agent: str,
    ) -> None:
        self._transport = transport
        self._authorization = authorization
        self._base_url = base_url
        self._default_country = default_country
        self._max_retries = max_retries
        self._user_agent = user_agent

    def request(
        self,
        method: str,
        path: str,
        *,
        country: str | None = None,
        body: Mapping[str, Any] | None = None,
        query: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        cc = (country if country is not None else self._default_country).lower()
        if cc == "":
            raise ConfigurationError(
                "No country given for this call and no default set on the client."
            )

        url = f"{self._base_url}/{quote(cc, safe='')}/v1/{path.lstrip('/')}"
        if query is not None:
            filtered = {k: v for k, v in query.items() if v is not None}
            if filtered:
                url += "?" + urlencode(filtered)

        request_id = generate_request_id()
        headers: dict[str, str] = {
            "Authorization": self._authorization,
            "Accept": "application/json",
            "User-Agent": self._user_agent,
            "X-Request-Id": request_id,
        }

        payload: str | None = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json_encode(body)

        req = Request(method, url, headers, payload)

        attempt = 0
        while True:
            try:
                response = self._transport(req)
            except NetworkError:
                if attempt < self._max_retries:
                    self._backoff(attempt)
                    attempt += 1
                    continue
                raise

            if response.status_code in _RETRY_STATUSES and attempt < self._max_retries:
                self._backoff(attempt)
                attempt += 1
                continue

            return self._handle(response, request_id)

    def _handle(self, response: Response, request_id: str) -> dict[str, Any]:
        envelope = json_decode(response.body) or {}
        status = response.status_code
        env_status = envelope.get("status")

        if status >= 400 or env_status in ("error", "failed"):
            if "request_id" not in envelope:
                envelope["request_id"] = request_id
            raise ApiError.from_envelope(status, envelope)

        return envelope

    def _backoff(self, attempt: int) -> None:
        time.sleep(_BASE_DELAY_S * (2**attempt))
