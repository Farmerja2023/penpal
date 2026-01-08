from .adapters import BaseAdapter
from .exceptions import PaymentError


class PaymentProcessor:
    """Thin wrapper around an adapter implementing payment operations."""

    def __init__(self, adapter: BaseAdapter):
        if not isinstance(adapter, BaseAdapter):
            raise PaymentError("adapter must be a BaseAdapter")
        self.adapter = adapter

    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        if amount_cents <= 0:
            raise PaymentError("amount_cents must be > 0")
        return self.adapter.charge(amount_cents, currency, source, description)

    def refund(self, charge_id: str, amount_cents: int | None = None) -> dict:
        if not charge_id:
            raise PaymentError("charge_id required")
        return self.adapter.refund(charge_id, amount_cents)

    def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        return self.adapter.verify_webhook(payload, signature, secret)
