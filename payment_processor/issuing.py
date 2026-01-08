import uuid
from typing import Optional

from .exceptions import PaymentError, AdapterError


class IssuingProcessor:
    """Wrapper around an issuing adapter for virtual prepaid cards."""

    def __init__(self, adapter):
        # duck-typed: adapter must implement creating cardholders, issuing cards, loading funds, etc.
        self.adapter = adapter

    def create_cardholder(self, name: str, email: Optional[str] = None) -> dict:
        if not name:
            raise PaymentError("name required")
        return self.adapter.create_cardholder(name=name, email=email)

    def issue_virtual_card(self, cardholder_id: str, currency: str = "USD", initial_balance_cents: int = 0) -> dict:
        if not cardholder_id:
            raise PaymentError("cardholder_id required")
        return self.adapter.issue_virtual_card(cardholder_id=cardholder_id, currency=currency, initial_balance_cents=int(initial_balance_cents))

    def load_funds(self, card_id: str, amount_cents: int) -> dict:
        if amount_cents <= 0:
            raise PaymentError("amount_cents must be > 0")
        return self.adapter.load_funds(card_id=card_id, amount_cents=int(amount_cents))

    def get_card(self, card_id: str) -> dict:
        if not card_id:
            raise PaymentError("card_id required")
        return self.adapter.get_card(card_id)

    def freeze_card(self, card_id: str) -> dict:
        return self.adapter.freeze_card(card_id)

    def unfreeze_card(self, card_id: str) -> dict:
        return self.adapter.unfreeze_card(card_id)

    def close_card(self, card_id: str) -> dict:
        return self.adapter.close_card(card_id)


class MockIssuingAdapter:
    """A simple in-memory issuing adapter for development and tests.

    It simulates cardholders and virtual prepaid cards with balances.
    """

    def __init__(self):
        self.cardholders = {}
        self.cards = {}

    def create_cardholder(self, name: str, email: Optional[str] = None) -> dict:
        cid = f"ch_{uuid.uuid4().hex[:12]}"
        record = {"id": cid, "name": name, "email": email}
        self.cardholders[cid] = record
        return dict(record)

    def issue_virtual_card(self, cardholder_id: str, currency: str = "USD", initial_balance_cents: int = 0) -> dict:
        if cardholder_id not in self.cardholders:
            raise AdapterError("cardholder not found")
        card_id = f"vc_{uuid.uuid4().hex[:12]}"
        card = {
            "id": card_id,
            "cardholder_id": cardholder_id,
            "currency": currency.upper(),
            "balance_cents": int(initial_balance_cents),
            "status": "active",
        }
        self.cards[card_id] = card
        return dict(card)

    def load_funds(self, card_id: str, amount_cents: int) -> dict:
        if card_id not in self.cards:
            raise AdapterError("card not found")
        if amount_cents <= 0:
            raise AdapterError("amount must be > 0")
        card = self.cards[card_id]
        card["balance_cents"] += int(amount_cents)
        return {"id": card_id, "balance_cents": card["balance_cents"]}

    def get_card(self, card_id: str) -> dict:
        if card_id not in self.cards:
            raise AdapterError("card not found")
        return dict(self.cards[card_id])

    def freeze_card(self, card_id: str) -> dict:
        if card_id not in self.cards:
            raise AdapterError("card not found")
        self.cards[card_id]["status"] = "frozen"
        return {"id": card_id, "status": "frozen"}

    def unfreeze_card(self, card_id: str) -> dict:
        if card_id not in self.cards:
            raise AdapterError("card not found")
        self.cards[card_id]["status"] = "active"
        return {"id": card_id, "status": "active"}

    def close_card(self, card_id: str) -> dict:
        if card_id not in self.cards:
            raise AdapterError("card not found")
        self.cards[card_id]["status"] = "closed"
        return {"id": card_id, "status": "closed"}


class StripeIssuingAdapter:
    """Stripe Issuing adapter using the official `stripe` package.

    This adapter implements cardholder creation, virtual card issuance and
    card status management using Stripe Issuing. It does not implement a
    card-level "load_funds" operation because Stripe Issuing cards draw from
    your platform balance; funding flows typically require Stripe Treasury
    or platform top-ups. `load_funds` therefore raises NotImplementedError
    and documents the recommended approach.

    Usage:
      adapter = StripeIssuingAdapter(api_key=YOUR_SECRET_KEY)
      adapter.create_cardholder(...)
      adapter.issue_virtual_card(...)

    Note: actual calls require the `stripe` package to be installed and a
    valid API key with Issuing access.
    """

    def __init__(self, api_key: str):
        try:
            import stripe
        except Exception as exc:  # pragma: no cover - runtime import error
            raise AdapterError("stripe package is required for StripeIssuingAdapter") from exc
        self._stripe = stripe
        self._stripe.api_key = api_key

    def create_cardholder(self, name: str, email: Optional[str] = None) -> dict:
        params = {"type": "individual", "name": name}
        if email:
            params["email"] = email
        obj = self._stripe.issuing.Cardholder.create(**params)
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)

    def issue_virtual_card(self, cardholder_id: str, currency: str = "USD", initial_balance_cents: int = 0) -> dict:
        # Create a virtual card linked to the provided cardholder.
        params = {"cardholder": cardholder_id, "type": "virtual", "currency": currency.upper()}
        obj = self._stripe.issuing.Card.create(**params)
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)

    def load_funds(self, card_id: str, amount_cents: int = 0) -> dict:
        """Stripe Issuing does not provide a per-card load API.

        To fund Issuing cards you must top up your Stripe balance (for example
        via `stripe.Topup.create`) or use Stripe Treasury to move funds into a
        ledger that authorizes card spending. Implementing a secure, live
        top-up flow depends on your Stripe account setup and is intentionally
        left to the integrator. This method raises to make that explicit.
        """
        raise NotImplementedError(
            "load_funds is not implemented: use Stripe Top-ups or Treasury flows to fund Issuing cards"
        )

    def get_card(self, card_id: str) -> dict:
        obj = self._stripe.issuing.Card.retrieve(card_id)
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)

    def freeze_card(self, card_id: str) -> dict:
        obj = self._stripe.issuing.Card.modify(card_id, status="inactive")
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)

    def unfreeze_card(self, card_id: str) -> dict:
        obj = self._stripe.issuing.Card.modify(card_id, status="active")
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)

    def close_card(self, card_id: str) -> dict:
        obj = self._stripe.issuing.Card.modify(card_id, status="canceled")
        return obj.to_dict() if hasattr(obj, "to_dict") else dict(obj)
