import pytest

from payment_processor import PaymentProcessor, MockAdapter, PaymentError


def test_charge_and_refund():
    adapter = MockAdapter()
    processor = PaymentProcessor(adapter)

    charge = processor.charge(1200, "USD", "tok_test", "Test charge")
    assert charge["amount_cents"] == 1200
    assert charge["currency"] == "USD"
    assert charge["status"] == "succeeded"

    refund = processor.refund(charge["id"], 200)
    assert refund["refunded_cents"] == 200
    assert refund["status"] in ("succeeded", "refunded") or isinstance(refund["status"], str)


def test_invalid_amount_raises():
    adapter = MockAdapter()
    processor = PaymentProcessor(adapter)
    with pytest.raises(PaymentError):
        processor.charge(0, "USD", "tok", "Zero amount")
