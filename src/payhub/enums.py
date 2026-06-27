"""Payment and transfer status enumerations."""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

_E = TypeVar("_E", bound="_StrEnum")


class _StrEnum(str, Enum):
    """A string enum whose members compare equal to their string values."""

    @classmethod
    def try_from(cls: type[_E], value: str | None) -> _E | None:
        """Return the member for ``value`` or ``None`` for an unknown value.

        Mirrors PHP's ``BackedEnum::tryFrom`` so newly introduced statuses never
        raise — they simply hydrate as ``None``.
        """
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            return None


class PaymentStatus(_StrEnum):
    CREATED = "CREATED"
    AWAITING_OTP = "AWAITING_OTP"
    QUEUED_FOR_PROCESSING = "QUEUED_FOR_PROCESSING"
    PROCESSING_OPERATOR = "PROCESSING_OPERATOR"
    PROCESSING_SYSTEM = "PROCESSING_SYSTEM"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    COMPLIANCE_FLAGGED = "COMPLIANCE_FLAGGED"
    CANCELED = "CANCELED"

    def is_final(self) -> bool:
        """No further transitions: SUCCESSFUL, FAILED or CANCELED."""
        return self in (PaymentStatus.SUCCESSFUL, PaymentStatus.FAILED, PaymentStatus.CANCELED)


class TransferStatus(_StrEnum):
    CREATED = "CREATED"
    PROCESSING_OPERATOR = "PROCESSING_OPERATOR"
    PROCESSING_SYSTEM = "PROCESSING_SYSTEM"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    COMPLIANCE_FLAGGED = "COMPLIANCE_FLAGGED"
    REFUNDED = "REFUNDED"
    UNRESOLVED = "UNRESOLVED"

    def is_final(self) -> bool:
        """No further transitions: SUCCESSFUL, FAILED or REFUNDED."""
        return self in (TransferStatus.SUCCESSFUL, TransferStatus.FAILED, TransferStatus.REFUNDED)
