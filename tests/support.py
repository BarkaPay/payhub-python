"""Test support: a fake transport that records requests and replays responses."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from payhub.http import Request, Response


class FakeTransport:
    """Records the request and replays queued responses — no network."""

    def __init__(self, responses: list[Response | BaseException]) -> None:
        self._queue: list[Response | BaseException] = list(responses)
        self.requests: list[Request] = []

    @property
    def last_request(self) -> Request | None:
        return self.requests[-1] if self.requests else None

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        if not self._queue:
            raise RuntimeError("FakeTransport: no more queued responses.")
        nxt = self._queue.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt


def json_response(status: int, body: Mapping[str, Any]) -> Response:
    return Response(status, json.dumps(body))
