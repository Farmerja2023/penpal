import uuid
import hmac
import hashlib
from typing import Optional


class BaseAdapter:
    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        raise NotImplementedError()

    def refund(self, charge_id: str, amount_cents: Optional[int] = None) -> dict:
        raise NotImplementedError()

    def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        raise NotImplementedError()


class MockAdapter(BaseAdapter):
    """A simple in-memory adapter for local development and tests."""

    def __init__(self):
        self.charges = {}

    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        cid = f"ch_{uuid.uuid4().hex[:12]}"
        record = {
            "id": cid,
            "amount_cents": int(amount_cents),
            "currency": currency,
            "source": source,
            "description": description,
            "status": "succeeded",
            "refunded_cents": 0,
        }
        self.charges[cid] = record
        return dict(record)

    def refund(self, charge_id: str, amount_cents: Optional[int] = None) -> dict:
        if charge_id not in self.charges:
            return {"id": charge_id, "status": "not_found"}
        record = self.charges[charge_id]
        if amount_cents is None:
            amount_cents = record["amount_cents"] - record.get("refunded_cents", 0)
        amount_cents = int(amount_cents)
        record["refunded_cents"] = record.get("refunded_cents", 0) + amount_cents
        if record["refunded_cents"] >= record["amount_cents"]:
            record["status"] = "refunded"
        return {"id": charge_id, "refunded_cents": record["refunded_cents"], "status": record["status"]}

    def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, signature)


class StripeAdapter(BaseAdapter):
    """Lightweight stub for a Stripe-like adapter.

    This class is intentionally minimal and does not depend on the stripe package.
    It can be extended to call Stripe's HTTP API if desired.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        raise NotImplementedError("StripeAdapter.charge not implemented; extend for real API calls")

    def refund(self, charge_id: str, amount_cents: Optional[int] = None) -> dict:
        raise NotImplementedError("StripeAdapter.refund not implemented; extend for real API calls")

    def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        # Real implementation would verify stripe signature headers
        raise NotImplementedError("StripeAdapter.verify_webhook not implemented")
