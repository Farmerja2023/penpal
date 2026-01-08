import base64
import time
import hmac
import hashlib
import requests
from typing import Optional

from .adapters import BaseAdapter
from .exceptions import AdapterError


class StripeHTTPAdapter(BaseAdapter):
    """Adapter that talks to Stripe's HTTP API.

    Notes:
    - This implementation is minimal and supports creating a charge via the
      legacy Charges API for simplicity. In production prefer PaymentIntents.
    - `api_key` should be a secret key (starts with "sk_").
    - `webhook_secret` is the endpoint signing secret used to verify webhooks.
    """

    BASE = "https://api.stripe.com/v1"

    def __init__(self, api_key: str, webhook_secret: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.BASE}{path}"
        auth = (self.api_key, "")
        try:
            resp = requests.request(method, url, auth=auth, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise AdapterError(str(exc)) from exc
        if not resp.ok:
            # try to include body for debugging
            msg = f"stripe api error: {resp.status_code} {resp.text}"
            raise AdapterError(msg)
        return resp.json()

    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        data = {
            "amount": int(amount_cents),
            "currency": currency.lower(),
            "source": source,
            "description": description,
        }
        return self._request("POST", "/charges", data=data)

    def refund(self, charge_id: str, amount_cents: Optional[int] = None) -> dict:
        data = {}
        if amount_cents is not None:
            data["amount"] = int(amount_cents)
        return self._request("POST", f"/refunds", data={"charge": charge_id, **data})

    def verify_webhook(self, payload: bytes, signature: str, secret: str) -> bool:
        # Stripe signs payload as: <timestamp>.<payload>
        # signature header includes v1=<hexdigest>
        try:
            # header example: t=timestamp,v1=signature,v0=old
            parts = {k: v for k, v in (p.split("=") for p in signature.split(","))}
            ts = parts.get("t")
            sig = parts.get("v1")
        except Exception:
            return False
        signed_payload = ts.encode() + b"." + payload
        expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)


class PayPalHTTPAdapter(BaseAdapter):
    """Adapter for PayPal REST APIs (uses sandbox/production base depending on domain).

    This implementation performs basic token retrieval and a small payment flow
    using Orders API. It also supports verifying webhooks via PayPal's verify endpoint.
    """

    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True, timeout: float = 10.0):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.timeout = timeout
        self._token = None
        self._token_expiry = 0

    @property
    def base(self):
        return "https://api-m.sandbox.paypal.com" if self.sandbox else "https://api-m.paypal.com"

    def _auth(self):
        # get or refresh token
        if self._token and time.time() < self._token_expiry - 10:
            return self._token
        url = f"{self.base}/v1/oauth2/token"
        auth = (self.client_id, self.client_secret)
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        try:
            resp = requests.post(url, data={"grant_type": "client_credentials"}, auth=auth, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise AdapterError(str(exc)) from exc
        if not resp.ok:
            raise AdapterError(f"paypal token error: {resp.status_code} {resp.text}")
        body = resp.json()
        self._token = body["access_token"]
        self._token_expiry = time.time() + int(body.get("expires_in", 300))
        return self._token

    def _request(self, method: str, path: str, **kwargs):
        token = self._auth()
        url = f"{self.base}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        try:
            resp = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise AdapterError(str(exc)) from exc
        if not resp.ok:
            raise AdapterError(f"paypal api error: {resp.status_code} {resp.text}")
        return resp.json()

    def charge(self, amount_cents: int, currency: str, source: str, description: str = "") -> dict:
        # For PayPal, create an order and capture it. `source` is not used here—Push clients should create orders client-side.
        data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": currency.upper(), "value": f"{amount_cents/100:.2f}"},
                "description": description,
            }]
        }
        order = self._request("POST", "/v2/checkout/orders", json=data)
        # capture immediately
        order_id = order.get("id")
        if not order_id:
            raise AdapterError("paypal: no order id returned")
        capture = self._request("POST", f"/v2/checkout/orders/{order_id}/capture", json={})
        return {"order": order, "capture": capture}

    def refund(self, charge_id: str, amount_cents: Optional[int] = None) -> dict:
        # PayPal refunds are performed against captures; attempt refund endpoint
        data = {}
        if amount_cents is not None:
            data["amount"] = {"value": f"{amount_cents/100:.2f}"}
        return self._request("POST", f"/v2/payments/captures/{charge_id}/refund", json=data)

    def verify_webhook(self, payload: bytes, signature_headers: dict, webhook_id: str) -> bool:
        # PayPal requires a call to verify-webhook-signature
        token = self._auth()
        url = f"{self.base}/v1/notifications/verify-webhook-signature"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        body = {
            "transmission_id": signature_headers.get("paypal-transmission-id"),
            "transmission_time": signature_headers.get("paypal-transmission-time"),
            "cert_url": signature_headers.get("paypal-cert-url"),
            "auth_algo": signature_headers.get("paypal-auth-algo"),
            "transmission_sig": signature_headers.get("paypal-transmission-sig"),
            "webhook_id": webhook_id,
            "webhook_event": payload.decode() if isinstance(payload, (bytes, bytearray)) else payload,
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise AdapterError(str(exc)) from exc
        if not resp.ok:
            return False
        return resp.json().get("verification_status") == "SUCCESS"
