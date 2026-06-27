"""Resource namespaces exposed on the client (``client.payments`` etc.)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from ._util import as_dict, as_list_of_dict
from .errors import NotFoundError
from .models import (
    Balance,
    Pagination,
    Payment,
    PaymentList,
    Transfer,
    TransferList,
)

if TYPE_CHECKING:
    from .client import _ApiClient


class Payments:
    def __init__(self, api: _ApiClient) -> None:
        self._api = api

    def create(self, params: Mapping[str, Any], country: str | None = None) -> Payment:
        """Create a payment. ``params``: operator, phone_number, amount, order{…}, otp?"""
        env = self._api.request("POST", "payments", country=country, body=params)
        return Payment.from_dict(_unwrap(env, "payment"))

    def list(
        self,
        filters: Mapping[str, Any] | None = None,
        country: str | None = None,
    ) -> PaymentList:
        """List payments. ``filters``: status, operator, from_date, to_date, per_page, …"""
        env = self._api.request("GET", "payments", country=country, query=filters)
        return _payment_list(env)

    def get(self, id: str, country: str | None = None) -> Payment:
        """Look up a payment by its public_id (UUID) or your order_id."""
        env = self._api.request("GET", f"payments/{quote(id, safe='')}", country=country)
        data = as_dict(env, "data") or {}
        rows = as_list_of_dict(data, "payments") or []
        if rows:
            return Payment.from_dict(rows[0])
        raise NotFoundError(f'No payment found for "{id}".', "resource_not_found", 404)

    def confirm_otp(self, public_id: str, otp: str, country: str | None = None) -> Payment:
        """Confirm a payment that is AWAITING_OTP (operators that require an OTP step)."""
        env = self._api.request(
            "POST",
            f"payments/{quote(public_id, safe='')}/confirm-otp",
            country=country,
            body={"otp": otp},
        )
        return Payment.from_dict(_unwrap(env, "payment"))

    def resend_otp(self, public_id: str, country: str | None = None) -> None:
        self._api.request(
            "POST",
            f"payments/{quote(public_id, safe='')}/resend-otp",
            country=country,
        )


class Transfers:
    def __init__(self, api: _ApiClient) -> None:
        self._api = api

    def create(self, params: Mapping[str, Any], country: str | None = None) -> Transfer:
        """Create a transfer. ``params``: operator, phone_number, amount, order{…},
        ignore_double_spend_risk?"""
        env = self._api.request("POST", "transfers", country=country, body=params)
        return Transfer.from_dict(_unwrap(env, "transfer"))

    def list(
        self,
        filters: Mapping[str, Any] | None = None,
        country: str | None = None,
    ) -> TransferList:
        env = self._api.request("GET", "transfers", country=country, query=filters)
        return _transfer_list(env)

    def get(self, id: str, country: str | None = None) -> Transfer:
        """Look up a transfer by its public_id (UUID) or your order_id."""
        env = self._api.request("GET", f"transfers/{quote(id, safe='')}", country=country)
        data = as_dict(env, "data") or {}
        rows = as_list_of_dict(data, "transfers") or []
        if rows:
            return Transfer.from_dict(rows[0])
        raise NotFoundError(f'No transfer found for "{id}".', "resource_not_found", 404)


class BalanceResource:
    def __init__(self, api: _ApiClient) -> None:
        self._api = api

    def get(self, country: str | None = None) -> Balance:
        """The merchant's wallet balance for the country."""
        env = self._api.request("GET", "balance", country=country)
        return Balance.from_dict(as_dict(env, "data") or {})


class Operators:
    def __init__(self, api: _ApiClient) -> None:
        self._api = api

    def availability(self, country: str | None = None) -> dict[str, Any]:
        """Real-time payment/transfer availability per operator."""
        env = self._api.request("GET", "operators/availability", country=country)
        return as_dict(env, "data") or {}

    def info(self, country: str | None = None) -> dict[str, Any]:
        """Operator capabilities (OTP requirement, amount bounds, instructions).

        This is the authoritative list of operators for the country.
        """
        env = self._api.request("GET", "operators/info", country=country)
        return as_dict(env, "data") or {}


def _unwrap(envelope: Mapping[str, Any], key: str) -> dict[str, Any]:
    data = as_dict(envelope, "data") or {}
    return as_dict(data, key) or {}


def _payment_list(envelope: Mapping[str, Any]) -> PaymentList:
    data = as_dict(envelope, "data") or {}
    rows = as_list_of_dict(data, "payments") or []
    items = [Payment.from_dict(row) for row in rows]
    meta = as_dict(envelope, "meta")
    return PaymentList(items, Pagination.from_dict(meta) if meta is not None else None)


def _transfer_list(envelope: Mapping[str, Any]) -> TransferList:
    data = as_dict(envelope, "data") or {}
    rows = as_list_of_dict(data, "transfers") or []
    items = [Transfer.from_dict(row) for row in rows]
    meta = as_dict(envelope, "meta")
    return TransferList(items, Pagination.from_dict(meta) if meta is not None else None)
