"""Disburse a transfer (payout). Run: PAYHUB_API_KEY=... python examples/disburse.py"""

from __future__ import annotations

import os
import sys
import time

import payhub
from payhub import ConflictError, PayHubError

client = payhub.PayHub(
    api_key=os.environ.get("PAYHUB_API_KEY", "pk_live_xxx:sk_live_yyy"),
    country="bf",
)

try:
    transfer = client.transfers.create(
        {
            "operator": "ORANGE",
            "phone_number": "50123456789",
            "amount": 50000,
            "order": {"id": f"XFER-{int(time.time())}"},
        }
    )
    status = transfer.status.value if transfer.status else "unknown"
    print(f"Transfer {transfer.public_id} — status {status}")
except ConflictError as exc:
    # The 60s duplicate guard fired — a near-identical transfer is already in flight.
    print(f"Duplicate transfer: {exc}", file=sys.stderr)
except PayHubError as exc:
    print(f"PayHub error: {exc}", file=sys.stderr)
