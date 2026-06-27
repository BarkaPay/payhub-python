"""The exception hierarchy raised by the SDK.

Catch everything from the SDK with :class:`PayHubError`. API errors map the most
common cases to :class:`ApiError` subclasses so you can catch them precisely.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class PayHubError(Exception):
    """Base class for every exception the SDK raises."""


class ApiError(PayHubError):
    """Base class for every error returned by the PayHub API (any response with
    the standard error envelope or a non-2xx status)."""

    def __init__(
        self,
        message: str,
        code: str = "",
        http_status: int = 0,
        request_id: str | None = None,
        errors: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        #: Machine-readable code from the envelope (e.g. ``validation_error``).
        self.code = code
        self.http_status = http_status
        #: Correlation id echoed by the API — quote it to support.
        self.request_id = request_id
        #: Field-level details (validation) or context.
        self.errors: dict[str, Any] = dict(errors) if errors else {}

    @classmethod
    def from_envelope(cls, http_status: int, envelope: Mapping[str, Any]) -> ApiError:
        """Build the most specific exception for an error envelope."""
        raw_code = envelope.get("code")
        code = raw_code if isinstance(raw_code, str) else ""

        raw_message = envelope.get("message")
        message = (
            raw_message
            if isinstance(raw_message, str) and raw_message != ""
            else f"PayHub API error (HTTP {http_status})."
        )

        raw_request_id = envelope.get("request_id")
        request_id = raw_request_id if isinstance(raw_request_id, str) else None

        raw_errors = envelope.get("errors")
        errors = raw_errors if isinstance(raw_errors, dict) else {}

        error_cls = _class_for(code, http_status)
        return error_cls(message, code, http_status, request_id, errors)


class AuthenticationError(ApiError):
    """401 — missing or invalid credentials."""


class AuthorizationError(ApiError):
    """403 / 410 / 451 — authenticated, but not allowed (scope, IP, account state)."""


class ValidationError(ApiError):
    """422 — request validation failed. ``errors`` holds the field → messages map."""


class NotFoundError(ApiError):
    """404 — unknown endpoint, country, or resource."""


class ConflictError(ApiError):
    """409 — duplicate / already-exists (e.g. the 60s duplicate-transfer guard)."""


class RateLimitError(ApiError):
    """429 — rate limit reached. Safe to retry with backoff."""


class ServiceUnavailableError(ApiError):
    """503 — operator or service temporarily unavailable. Retryable."""


class ServerError(ApiError):
    """5xx — unexpected server error on PayHub's side."""


class NetworkError(PayHubError):
    """The HTTP request never completed (DNS, connection, timeout). No response."""


class SignatureVerificationError(PayHubError):
    """A webhook signature could not be verified (bad signature, stale, malformed)."""


class ConfigurationError(PayHubError):
    """The SDK was constructed or called with invalid arguments."""


_CODE_MAP: dict[str, type[ApiError]] = {
    "unauthenticated": AuthenticationError,
    "invalid_api_key": AuthenticationError,
    "incorrect_credentials": AuthenticationError,
    "unauthorized": AuthorizationError,
    "ip_not_allowed": AuthorizationError,
    "merchant_suspended": AuthorizationError,
    "merchant_closed": AuthorizationError,
    "validation_error": ValidationError,
    "invalid_input": ValidationError,
    "resource_not_found": NotFoundError,
    "duplicate_transaction": ConflictError,
    "resource_already_exists": ConflictError,
    "too_many_requests": RateLimitError,
    "service_unavailable": ServiceUnavailableError,
    "operator_unavailable": ServiceUnavailableError,
}

_STATUS_MAP: dict[int, type[ApiError]] = {
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
    503: ServiceUnavailableError,
}


def _class_for(code: str, http_status: int) -> type[ApiError]:
    mapped = _CODE_MAP.get(code)
    if mapped is not None:
        return mapped
    by_status = _STATUS_MAP.get(http_status)
    if by_status is not None:
        return by_status
    if http_status >= 500:
        return ServerError
    return ApiError
