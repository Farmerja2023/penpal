from flask import Flask, request, jsonify
from payment_processor.adapters_http import StripeHTTPAdapter, PayPalHTTPAdapter
import os

app = Flask(__name__)

# Configure via env vars
STRIPE_SECRET = os.environ.get("STRIPE_SECRET")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID")

stripe_adapter = StripeHTTPAdapter(api_key=STRIPE_API_KEY or "", webhook_secret=STRIPE_SECRET)
paypal_adapter = PayPalHTTPAdapter(client_id=PAYPAL_CLIENT_ID or "", client_secret=PAYPAL_CLIENT_SECRET or "")


@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    secret = STRIPE_SECRET or ""
    ok = stripe_adapter.verify_webhook(payload, sig_header, secret)
    if not ok:
        return jsonify({"ok": False}), 400
    return jsonify({"ok": True})


@app.route("/webhook/paypal", methods=["POST"])
def paypal_webhook():
    payload = request.get_data()
    headers = {
        "paypal-transmission-id": request.headers.get("Paypal-Transmission-Id"),
        "paypal-transmission-time": request.headers.get("Paypal-Transmission-Time"),
        "paypal-cert-url": request.headers.get("Paypal-Cert-Url"),
        "paypal-auth-algo": request.headers.get("Paypal-Auth-Algo"),
        "paypal-transmission-sig": request.headers.get("Paypal-Transmission-Sig"),
    }
    ok = paypal_adapter.verify_webhook(payload, headers, PAYPAL_WEBHOOK_ID or "")
    if not ok:
        return jsonify({"ok": False}), 400
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=8000)
