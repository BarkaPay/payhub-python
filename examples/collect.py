"""Collect a payment (mobile money). Run: PAYHUB_API_KEY=... python examples/collect.py"""

from __future__ import annotations

import os
import sys
import time

import payhub
from payhub import PayHubError

client = payhub.PayHub(
    api_key=os.environ.get("PAYHUB_API_KEY", "pk_live_xxx:sk_live_yyy"),
    country="bf",
)

try:
    # The OTP field is only needed for synchronous-OTP operators (e.g. Orange);
    # most async operators (MTN, Wave) return PROCESSING_OPERATOR and complete
    # via webhook. Always branch on the returned status.
    payment = client.payments.create(
        {
            "operator": "ORANGE",
            "phone_number": "50123456789",
            "amount": 10000,
            "otp": "123456",
            "order": {"id": f"ORDER-{int(time.time())}"},
        }
    )
    status = payment.status.value if payment.status else "unknown"
    print(f"Payment {payment.public_id} — status {status}")
except PayHubError as exc:
    print(f"PayHub error: {exc}", file=sys.stderr)
