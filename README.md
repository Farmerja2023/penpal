```markdown
# penpal

## Payment processor

This repo now includes a minimal payment processor package under `payment_processor`.

- Demo: `python3 scripts/demo.py`
- Tests: `pytest -q`

Live Issuing (Stripe)
---------------------

The issuing demo supports a live mode backed by Stripe Issuing. Use these
environment variables to enable live operations:

- `STRIPE_API_KEY`: your Stripe secret key (starts with `sk_live_...`). If set, the demo will try to use `StripeIssuingAdapter`.
- `STRIPE_LIVE`: set to `1` or `true` to indicate you intend live operations; the adapter will validate key shape.
- `STRIPE_DO_TOPUP`: set to `1` to perform a real top-up when running `scripts/demo_issuing.py` (disabled by default for safety).
- `STRIPE_TOPUP_AMOUNT_CENTS`: amount of the top-up in cents (defaults to `1000`).

Important safety notes:

- Top-ups move real money when used with a live key. Ensure your Stripe account is configured with a funding source before calling `load_funds`.
- The adapter will raise an error if `live=True` is set but the key looks like a test key (starts with `sk_test`).

Demo usage examples:

```bash
# Mock/demo mode (safe):
python3 scripts/demo_issuing.py

# Live issuing (no automatic top-up):
STRIPE_API_KEY=sk_live_... STRIPE_LIVE=1 python3 scripts/demo_issuing.py

# Live issuing with a real top-up (this moves funds):
STRIPE_API_KEY=sk_live_... STRIPE_LIVE=1 STRIPE_DO_TOPUP=1 STRIPE_TOPUP_AMOUNT_CENTS=5000 python3 scripts/demo_issuing.py
```

```
# penpal