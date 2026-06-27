"""Official Python client for the PayHub payments API.

Quick start::

    import payhub

    client = payhub.PayHub(api_key="pk_live_xxx:sk_live_yyy", country="bf")
    payment = client.payments.create({
        "operator": "ORANGE",
        "phone_number": "50123456789",
        "amount": 10000,
        "order": {"id": "ORDER-2026-001"},
    })
    print(payment.public_id, payment.status)
"""

from __future__ import annotations

from . import webhook
from ._version import __version__
from .client import PayHub
from .enums import PaymentStatus, TransferStatus
from .errors import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    PayHubError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
    SignatureVerificationError,
    ValidationError,
)
from .http import Request, Response, Transport, UrllibTransport
from .models import (
    Balance,
    Pagination,
    Payment,
    PaymentList,
    Transfer,
    TransferList,
)

__all__ = [
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "Balance",
    "ConfigurationError",
    "ConflictError",
    "NetworkError",
    "NotFoundError",
    "Pagination",
    "PayHub",
    # errors
    "PayHubError",
    # models
    "Payment",
    "PaymentList",
    # enums
    "PaymentStatus",
    "RateLimitError",
    # http
    "Request",
    "Response",
    "ServerError",
    "ServiceUnavailableError",
    "SignatureVerificationError",
    "Transfer",
    "TransferList",
    "TransferStatus",
    "Transport",
    "UrllibTransport",
    "ValidationError",
    "__version__",
    "webhook",
]
