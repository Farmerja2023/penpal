import types

from payment_processor.issuing import StripeIssuingAdapter


def test_reconcile_calls_update_fn(monkeypatch):
    adapter = StripeIssuingAdapter.__new__(StripeIssuingAdapter)

    class FakeTopupObj:
        def __init__(self, id, amount, currency, status, created, metadata):
            self._d = {"id": id, "amount": amount, "currency": currency, "status": status, "created": created, "metadata": metadata}

        def to_dict(self):
            return self._d

    class FakeTopupList:
        data = [FakeTopupObj("tu_1", 1000, "usd", "succeeded", 1700000000, {"card_id": "vc_1"}),
                FakeTopupObj("tu_2", 2000, "usd", "succeeded", 1700000100, {})]

    fake_stripe = types.SimpleNamespace(Topup=types.SimpleNamespace(list=lambda **kw: FakeTopupList))
    adapter._stripe = fake_stripe

    seen = []

    def updater(card_id, amount, topup_id):
        seen.append((card_id, amount, topup_id))

    res = StripeIssuingAdapter.reconcile_topups(adapter, since=1700000000, update_fn=updater)
    assert isinstance(res, list)
    # only one topup had metadata.card_id
    assert len(seen) == 1
    assert seen[0] == ("vc_1", 1000, "tu_1")
