from __future__ import annotations

from payhub import Balance, Payment, PaymentStatus, TransferStatus


def test_payment_hydrates_and_keeps_raw() -> None:
    payment = Payment.from_dict(
        {
            "public_id": "pay_9",
            "amount": 10000,
            "fees": "250.00",
            "currency": "XOF",
            "status": "AWAITING_OTP",
            "order_id": "O-1",
            "future_field": "kept",
        }
    )

    assert payment.public_id == "pay_9"
    assert payment.amount == 10000
    assert payment.fees == "250.00"
    assert payment.status is PaymentStatus.AWAITING_OTP
    assert payment.order_id == "O-1"
    assert payment.reason is None
    assert payment.raw["future_field"] == "kept"


def test_payment_unknown_status_becomes_none() -> None:
    payment = Payment.from_dict({"public_id": "p", "status": "SOMETHING_NEW"})
    assert payment.status is None


def test_balance_fiat_and_crypto_shapes() -> None:
    fiat = Balance.from_dict({"country": "BF", "currency": "XOF", "available": "1500.00"})
    assert fiat.available == "1500.00"
    assert fiat.balances is None

    crypto = Balance.from_dict(
        {
            "country": "CC",
            "balances": [{"asset": "USDT", "network": "TRC20", "available": "12.50"}],
        }
    )
    assert crypto.balances is not None
    assert len(crypto.balances) == 1
    assert crypto.balances[0]["asset"] == "USDT"


def test_status_finality() -> None:
    assert PaymentStatus.SUCCESSFUL.is_final()
    assert not PaymentStatus.PROCESSING_OPERATOR.is_final()
    assert TransferStatus.REFUNDED.is_final()
    assert not TransferStatus.CREATED.is_final()


def test_payment_is_frozen() -> None:
    payment = Payment.from_dict({"public_id": "p"})
    try:
        payment.public_id = "other"  # type: ignore[misc]
        raise AssertionError("expected dataclasses.FrozenInstanceError")
    except Exception as exc:  # FrozenInstanceError is a subclass of AttributeError
        assert exc.__class__.__name__ == "FrozenInstanceError"
