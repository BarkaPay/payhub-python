"""Transport layer.

The SDK ships a zero-dependency :class:`UrllibTransport` built on the standard
library. Inject your own callable (anything matching :class:`Transport`) to plug
in a different HTTP stack — or to fake the network in tests.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .errors import NetworkError


@dataclass(frozen=True)
class Request:
    """An outbound HTTP request — a plain value object."""

    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: str | None = None


@dataclass(frozen=True)
class Response:
    """A raw HTTP response returned by a :class:`Transport`."""

    status_code: int
    body: str
    headers: Mapping[str, str] = field(default_factory=dict)


@runtime_checkable
class Transport(Protocol):
    """Callable contract for the transport.

    Implement it as a function ``def transport(request: Request) -> Response`` or
    as any object with a matching ``__call__``.
    """

    def __call__(self, request: Request) -> Response:  # pragma: no cover - protocol
        ...


class UrllibTransport:
    """Zero-dependency HTTP transport built on ``urllib.request``."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def __call__(self, request: Request) -> Response:
        data = request.body.encode("utf-8") if request.body is not None else None
        req = urllib.request.Request(
            url=request.url,
            data=data,
            method=request.method,
        )
        for name, value in request.headers.items():
            req.add_header(name, value)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return Response(int(resp.status), body, _lower_headers(resp.headers.items()))
        except urllib.error.HTTPError as exc:
            # 4xx/5xx still carry the error envelope — surface it as a Response so
            # the API client can map it to a typed exception.
            raw = exc.read()
            body = raw.decode("utf-8", errors="replace") if raw else ""
            headers = _lower_headers(exc.headers.items()) if exc.headers else {}
            return Response(int(exc.code), body, headers)
        except urllib.error.URLError as exc:
            raise NetworkError(str(exc.reason)) from exc
        except (TimeoutError, OSError) as exc:  # pragma: no cover - network edge
            raise NetworkError(str(exc)) from exc


def _lower_headers(items: object) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in items:  # type: ignore[attr-defined]
        result[str(name).lower()] = str(value)
    return result
