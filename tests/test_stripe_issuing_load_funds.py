import types
import pytest

from payment_processor.issuing import StripeIssuingAdapter, AdapterError


def test_load_funds_creates_topup(monkeypatch):
    adapter = StripeIssuingAdapter.__new__(StripeIssuingAdapter)
    # create a fake stripe module with Topup.create
    class FakeTopup:
        @staticmethod
        def create(amount, currency, description=None, metadata=None):
            class R:
                def to_dict(self):
                    return {"id": "tu_fake", "amount": amount, "currency": currency, "description": description, "metadata": metadata}

            return R()

    fake_stripe = types.SimpleNamespace(Topup=FakeTopup)
    adapter._stripe = fake_stripe
    # call load_funds and verify result
    res = StripeIssuingAdapter.load_funds(adapter, "card_123", 1500, currency="USD", description="top-up")
    assert res["id"] == "tu_fake"
    assert res["amount"] == 1500
    assert res["metadata"]["card_id"] == "card_123"


def test_live_mode_validation_raises_for_test_key():
    with pytest.raises(AdapterError):
        StripeIssuingAdapter(api_key="sk_test_abc", live=True)
