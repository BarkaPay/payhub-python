"""Read the merchant wallet balance. Run: PAYHUB_API_KEY=... python examples/balance.py"""

from __future__ import annotations

import os
import sys

import payhub
from payhub import PayHubError

client = payhub.PayHub(
    api_key=os.environ.get("PAYHUB_API_KEY", "pk_live_xxx:sk_live_yyy"),
    country="bf",
)

try:
    balance = client.balance.get()

    if balance.balances is not None:
        # Crypto (cc): one entry per asset/network.
        for entry in balance.balances:
            asset = entry.get("asset", "?")
            network = entry.get("network", "?")
            available = entry.get("available", "0")
            print(f"{asset}/{network}: {available}")
    else:
        print(f"Available: {balance.available or '0'} {balance.currency or ''}")
except PayHubError as exc:
    print(f"PayHub error: {exc}", file=sys.stderr)
