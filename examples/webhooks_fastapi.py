from fastapi import FastAPI, Request, Header, HTTPException
from payment_processor.adapters_http import StripeHTTPAdapter, PayPalHTTPAdapter
import os

app = FastAPI()

STRIPE_SECRET = os.environ.get("STRIPE_SECRET")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID")

stripe_adapter = StripeHTTPAdapter(api_key=STRIPE_API_KEY or "", webhook_secret=STRIPE_SECRET)
paypal_adapter = PayPalHTTPAdapter(client_id=PAYPAL_CLIENT_ID or "", client_secret=PAYPAL_CLIENT_SECRET or "")


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(None)):
    payload = await request.body()
    if not stripe_adapter.verify_webhook(payload, stripe_signature or "", STRIPE_SECRET or ""):
        raise HTTPException(status_code=400, detail="invalid signature")
    return {"ok": True}


@app.post("/webhook/paypal")
async def paypal_webhook(request: Request,
                         paypal_transmission_id: str | None = Header(None),
                         paypal_transmission_time: str | None = Header(None),
                         paypal_cert_url: str | None = Header(None),
                         paypal_auth_algo: str | None = Header(None),
                         paypal_transmission_sig: str | None = Header(None)):
    payload = await request.body()
    headers = {
        "paypal-transmission-id": paypal_transmission_id,
        "paypal-transmission-time": paypal_transmission_time,
        "paypal-cert-url": paypal_cert_url,
        "paypal-auth-algo": paypal_auth_algo,
        "paypal-transmission-sig": paypal_transmission_sig,
    }
    ok = paypal_adapter.verify_webhook(payload, headers, PAYPAL_WEBHOOK_ID or "")
    if not ok:
        raise HTTPException(status_code=400, detail="invalid signature")
    return {"ok": True}
