#!/usr/bin/env python3
"""Validation script: Check if live issuing mode is properly configured.

Usage:
  python3 scripts/validate_live_mode.py

This script checks that:
- ENABLE_LIVE_MODE is set (required)
- STRIPE_API_KEY is set and looks like a live key (sk_live_...)
- STRIPE_LIVE is set to 1 (if you want live behavior)
"""
import os
import sys


def validate():
    """Validate live issuing configuration."""
    issues = []
    warnings = []

    enable_live = os.environ.get("ENABLE_LIVE_MODE", "").lower() in ("1", "true", "yes")
    stripe_key = os.environ.get("STRIPE_API_KEY", "").strip()
    stripe_live_flag = os.environ.get("STRIPE_LIVE", "").lower() in ("1", "true", "yes")
    do_topup = os.environ.get("STRIPE_DO_TOPUP", "").lower() in ("1", "true", "yes")

    print("=" * 60)
    print("Live Issuing Mode Validation")
    print("=" * 60)

    # Check ENABLE_LIVE_MODE
    print(f"ENABLE_LIVE_MODE: {enable_live}")
    if not enable_live:
        issues.append("ENABLE_LIVE_MODE is not set. Set to '1' to enable live operations.")

    # Check STRIPE_API_KEY
    print(f"STRIPE_API_KEY: {stripe_key[:20]}..." if stripe_key else "STRIPE_API_KEY: (not set)")
    if not stripe_key:
        issues.append("STRIPE_API_KEY is not set. Obtain from https://dashboard.stripe.com/apikeys")
    elif not stripe_key.startswith("sk_"):
        issues.append("STRIPE_API_KEY does not look like a Stripe key (should start with 'sk_').")
    elif stripe_key.startswith("sk_test") and enable_live:
        warnings.append("STRIPE_API_KEY looks like a test key (sk_test_...) but ENABLE_LIVE_MODE=1. Test keys will fail in live mode.")

    # Check STRIPE_LIVE
    print(f"STRIPE_LIVE: {stripe_live_flag}")
    if not stripe_live_flag:
        warnings.append("STRIPE_LIVE is not set. Live card operations will fall back to mock adapter.")

    # Check STRIPE_DO_TOPUP
    if do_topup:
        print(f"STRIPE_DO_TOPUP: {do_topup} (real top-ups will be performed)")
        topup_amount = os.environ.get("STRIPE_TOPUP_AMOUNT_CENTS", "1000")
        print(f"STRIPE_TOPUP_AMOUNT_CENTS: {topup_amount} cents (${int(topup_amount)/100:.2f})")
        if enable_live and stripe_key.startswith("sk_live"):
            warnings.append("STRIPE_DO_TOPUP is enabled with a live key. Top-ups will move REAL MONEY.")
    else:
        print("STRIPE_DO_TOPUP: 0 (disabled; top-ups will not run)")

    print("\n" + "=" * 60)
    if issues:
        print("❌ ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    if not issues and not warnings:
        print("✅ Configuration looks good!")

    print("=" * 60)

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(validate())
