"""Typed data objects returned by the SDK.

Documented fields are typed; every object keeps the full payload in ``raw`` for
forward-compatibility, so a field the API adds tomorrow is never lost.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from ._util import as_amount, as_dict, as_int, as_list_of_dict, as_str
from .enums import PaymentStatus, TransferStatus


@dataclass(frozen=True)
class Payment:
    """A collection (payment) as returned by the API."""

    public_id: str
    amount: int | float | str | None
    fees: str | None
    currency: str | None
    phone_number: str | None
    country: str | None
    operator: str | None
    channel: str | None
    status: PaymentStatus | None
    order_id: str | None
    provider_transaction_id: str | None
    order_data: dict[str, Any] | None
    reason: str | None
    created_at: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Payment:
        return cls(
            public_id=as_str(data, "public_id") or "",
            amount=as_amount(data, "amount"),
            fees=as_str(data, "fees"),
            currency=as_str(data, "currency"),
            phone_number=as_str(data, "phone_number"),
            country=as_str(data, "country"),
            operator=as_str(data, "operator"),
            channel=as_str(data, "channel"),
            status=PaymentStatus.try_from(as_str(data, "status")),
            order_id=as_str(data, "order_id"),
            provider_transaction_id=as_str(data, "provider_transaction_id"),
            order_data=as_dict(data, "order_data"),
            reason=as_str(data, "reason"),
            created_at=as_str(data, "created_at"),
            raw=dict(data),
        )


@dataclass(frozen=True)
class Transfer:
    """A disbursement (transfer) as returned by the API."""

    public_id: str
    amount: int | float | str | None
    fees: str | None
    currency: str | None
    phone_number: str | None
    country: str | None
    operator: str | None
    channel: str | None
    status: TransferStatus | None
    order_id: str | None
    provider_transaction_id: str | None
    order_data: dict[str, Any] | None
    reason: str | None
    created_at: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Transfer:
        return cls(
            public_id=as_str(data, "public_id") or "",
            amount=as_amount(data, "amount"),
            fees=as_str(data, "fees"),
            currency=as_str(data, "currency"),
            phone_number=as_str(data, "phone_number"),
            country=as_str(data, "country"),
            operator=as_str(data, "operator"),
            channel=as_str(data, "channel"),
            status=TransferStatus.try_from(as_str(data, "status")),
            order_id=as_str(data, "order_id"),
            provider_transaction_id=as_str(data, "provider_transaction_id"),
            order_data=as_dict(data, "order_data"),
            reason=as_str(data, "reason"),
            created_at=as_str(data, "created_at"),
            raw=dict(data),
        )


@dataclass(frozen=True)
class Balance:
    """The merchant wallet balance for a country.

    Fiat wallets fill ``currency`` + ``available``/``total``/``holds`` (decimal
    strings). Crypto (``cc``) instead fills ``balances``, one entry per
    asset/network.
    """

    country: str | None
    currency: str | None
    available: str | None
    total: str | None
    holds: str | None
    balances: list[dict[str, Any]] | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Balance:
        return cls(
            country=as_str(data, "country"),
            currency=as_str(data, "currency"),
            available=as_str(data, "available"),
            total=as_str(data, "total"),
            holds=as_str(data, "holds"),
            balances=as_list_of_dict(data, "balances"),
            raw=dict(data),
        )


@dataclass(frozen=True)
class Pagination:
    """Pagination metadata from a list response's ``meta`` block."""

    current_page: int | None
    last_page: int | None
    per_page: int | None
    total: int | None

    @classmethod
    def from_dict(cls, meta: Mapping[str, Any]) -> Pagination:
        return cls(
            current_page=as_int(meta, "current_page"),
            last_page=as_int(meta, "last_page"),
            per_page=as_int(meta, "per_page"),
            total=as_int(meta, "total"),
        )


@dataclass(frozen=True)
class PaymentList:
    """An iterable list of :class:`Payment` plus optional :class:`Pagination`."""

    items: list[Payment]
    meta: Pagination | None

    def __iter__(self) -> Iterator[Payment]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Payment:
        return self.items[index]


@dataclass(frozen=True)
class TransferList:
    """An iterable list of :class:`Transfer` plus optional :class:`Pagination`."""

    items: list[Transfer]
    meta: Pagination | None

    def __iter__(self) -> Iterator[Transfer]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> Transfer:
        return self.items[index]
