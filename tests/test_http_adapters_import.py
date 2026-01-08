def test_imports():
    # simple smoke test to ensure adapters and examples import correctly
    import payment_processor.adapters_http as http_adapters
    import examples.webhooks_flask as wf
    import examples.webhooks_fastapi as wfa
    assert hasattr(http_adapters, "StripeHTTPAdapter")
    assert hasattr(http_adapters, "PayPalHTTPAdapter")
    assert hasattr(wf, "app")
    assert hasattr(wfa, "app")
