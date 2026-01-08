"""Demo for virtual prepaid card issuing.

This script supports two modes:
- Mock mode (default) — uses `MockIssuingAdapter` and is safe to run.
- Live mode — uses `StripeIssuingAdapter` when `STRIPE_API_KEY` is set.

To perform a real top-up (live money), set `STRIPE_DO_TOPUP=1` and provide
`STRIPE_TOPUP_AMOUNT_CENTS` (defaults to 1000).
"""
import os
from payment_processor import IssuingProcessor, MockIssuingAdapter


def run_demo():
    stripe_key = os.environ.get("STRIPE_API_KEY")
    stripe_live_flag = os.environ.get("STRIPE_LIVE", "0").lower() in ("1", "true", "yes")
    enable_live_global = os.environ.get("ENABLE_LIVE_MODE", "0").lower() in ("1", "true", "yes")
    do_topup = os.environ.get("STRIPE_DO_TOPUP", "0").lower() in ("1", "true", "yes")
    topup_amount = int(os.environ.get("STRIPE_TOPUP_AMOUNT_CENTS", "1000"))

    if stripe_key:
        # create a StripeIssuingAdapter if stripe key provided; fall back to mock on error
        try:
            from payment_processor.issuing import StripeIssuingAdapter

            # require both the per-run flag and the repository-wide ENABLE_LIVE_MODE
            real_live = stripe_live_flag and enable_live_global
            if stripe_live_flag and not enable_live_global:
                print("Warning: STRIPE_LIVE requested but ENABLE_LIVE_MODE is not enabled. To enable set ENABLE_LIVE_MODE=1")
            adapter = StripeIssuingAdapter(api_key=stripe_key, live=real_live)
            print("Using StripeIssuingAdapter (live=%s)" % real_live)
        except Exception as exc:
            print("Failed to initialize StripeIssuingAdapter:", exc)
            print("Falling back to MockIssuingAdapter")
            adapter = MockIssuingAdapter()
    else:
        adapter = MockIssuingAdapter()
        print("Using MockIssuingAdapter (no STRIPE_API_KEY set)")

    issuing = IssuingProcessor(adapter)

    print("Creating cardholder Alice...")
    ch = issuing.create_cardholder("Alice Example", email="alice@example.com")
    print("Cardholder:", ch)

    print("Issuing virtual card (no initial balance)...")
    card = issuing.issue_virtual_card(ch["id"], currency="USD", initial_balance_cents=0)
    print("Card:", card)

    if do_topup:
        if not enable_live_global:
            print("STRIPE_DO_TOPUP requested but ENABLE_LIVE_MODE is not set — skipping top-up for safety.")
        else:
            print(f"Performing top-up of {topup_amount} cents (this will move real funds in live mode)...")
            loaded = issuing.load_funds(card["id"], topup_amount)
            print("Top-up result:", loaded)
    else:
        print("Skipping top-up. To enable top-up set STRIPE_DO_TOPUP=1 and provide STRIPE_TOPUP_AMOUNT_CENTS.")

    print("Freezing card...")
    print(issuing.freeze_card(card["id"]))

    print("Unfreezing card...")
    print(issuing.unfreeze_card(card["id"]))

    print("Closing card...")
    print(issuing.close_card(card["id"]))


if __name__ == "__main__":
    run_demo()
