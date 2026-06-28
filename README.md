# PayHub Python SDK

Official Python client for the [PayHub](https://payhub.africa/developers) payments API —
mobile money & crypto, one API across countries.

- **Zero runtime dependencies** — pure standard library (`urllib`, `hmac`, `json`).
- Typed payments, transfers and balance objects (frozen dataclasses, `py.typed`).
- Built-in webhook signature verification.
- Automatic retries on transient errors (429 / 503 / network).

## Requirements

Python **3.9+**.

## Install

```bash
pip install barkapay-payhub
```

The distribution is `barkapay-payhub`; you import it as `payhub`.

## Quick start

```python
import payhub

client = payhub.PayHub(
    api_key="pk_live_xxx:sk_live_yyy",  # the "key_id:secret" you copy from the dashboard
    country="bf",                        # default country, overridable per call
)

payment = client.payments.create({
    "operator": "ORANGE",
    "phone_number": "50123456789",
    "amount": 10000,
    "otp": "123456",                     # only for synchronous-OTP operators (e.g. Orange)
    "order": {"id": "ORDER-2026-001"},
})

print(payment.public_id, payment.status)
```

> **Authentication:** pass the raw `key_id:secret` (or `key_id` + `secret` separately).
> The SDK adds the `Bearer` prefix — never include the word `Bearer` yourself
> (an accidental one is forgiven).

## Payments

```python
client.payments.create({...})                          # -> payhub.Payment
client.payments.get("pay_… or order_id")               # by public_id or your order_id
client.payments.list({"status": "SUCCESSFUL", "per_page": 50})  # -> PaymentList (.items, .meta)
client.payments.confirm_otp(public_id, "123456")       # for AWAITING_OTP payments
client.payments.resend_otp(public_id)
```

The flow depends on the operator — always branch on the returned `status`:
synchronous (`SUCCESSFUL`/`FAILED`), `AWAITING_OTP` (confirm step), or
`PROCESSING_OPERATOR` (final outcome arrives by webhook).

```python
from payhub import PaymentStatus

if payment.status is PaymentStatus.AWAITING_OTP:
    payment = client.payments.confirm_otp(payment.public_id, otp)
```

## Transfers

```python
client.transfers.create({
    "operator": "ORANGE",
    "phone_number": "50123456789",
    "amount": 50000,
    "order": {"id": "XFER-2026-001"},
})
client.transfers.get(transfer_id)
client.transfers.list({"from_date": "2026-06-01"})     # -> TransferList
```

## Balance & operators

```python
balance = client.balance.get()    # payhub.Balance: available / total / holds / currency
client.operators.info()           # authoritative operator list for the country
client.operators.availability()
client.me()
```

## Webhooks

Verify the `PayHub-Signature` header against the **raw** request body:

```python
from payhub import webhook
from payhub import SignatureVerificationError

try:
    event = webhook.parse(
        raw_body,                            # bytes or str — the RAW body
        request.headers["PayHub-Signature"],
        endpoint_secret,                     # whsec_…
    )
except SignatureVerificationError:
    return Response(status=400)

# No `event` field — derive it from event["type"] + event["status"].
# Deduplicate on event["public_id"] (retries deliver the same body).
```

`webhook.verify(...)` returns a `bool` if you prefer not to catch.

## Errors

Every API error raises a typed exception extending `payhub.ApiError`
(`.code`, `.http_status`, `.request_id`, `.errors`):

| Exception | When |
|---|---|
| `AuthenticationError` | 401 — bad credentials |
| `AuthorizationError`  | 403/410/451 — not allowed |
| `ValidationError`     | 422 — bad request (`.errors`) |
| `NotFoundError`       | 404 |
| `ConflictError`       | 409 — duplicate |
| `RateLimitError`      | 429 |
| `ServiceUnavailableError` | 503 — retryable |
| `ServerError`         | 5xx |
| `NetworkError`        | request never reached a response |

Catch everything from the SDK with `payhub.PayHubError`.

## Configuration

```python
payhub.PayHub(
    api_key="key_id:secret",
    country="bf",
    base_url="https://hub.barkapay.com",
    max_retries=2,        # 429/503/network
    timeout=30.0,         # seconds
    transport=custom,     # any callable matching payhub.Transport (great for tests)
)
```

## License

MIT.
