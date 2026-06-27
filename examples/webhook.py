"""Minimal webhook receiver (Flask). Mount it at your registered endpoint URL.

Run: PAYHUB_WEBHOOK_SECRET=whsec_... flask --app examples/webhook run
"""

from __future__ import annotations

import os

from flask import Flask, Response, request  # type: ignore[import-not-found]

from payhub import SignatureVerificationError, webhook

app = Flask(__name__)
SECRET = os.environ.get("PAYHUB_WEBHOOK_SECRET", "whsec_xxx")


@app.post("/webhooks/payhub")
def payhub_webhook() -> Response:
    # Verify against the RAW body before trusting anything.
    try:
        event = webhook.parse(
            request.get_data(),  # raw bytes — do NOT use a re-encoded copy
            request.headers.get("PayHub-Signature", ""),
            SECRET,
        )
    except SignatureVerificationError:
        return Response("invalid signature", status=400)

    # There is no `event` field — derive it from `type` + `status`.
    event_type = event.get("type")
    status = event.get("status")
    public_id = event.get("public_id")

    # TODO: deduplicate on public_id (retries deliver the same body) and update
    # your order, e.g. (event_type == "payment" and status == "SUCCESSFUL").
    _ = (event_type, status, public_id)

    return Response("ok", status=200)
