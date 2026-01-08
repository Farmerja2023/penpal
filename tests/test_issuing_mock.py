from payment_processor import IssuingProcessor, MockIssuingAdapter, PaymentError


def test_issue_and_load_and_status():
    adapter = MockIssuingAdapter()
    issuing = IssuingProcessor(adapter)

    ch = issuing.create_cardholder("Bob")
    assert "id" in ch

    card = issuing.issue_virtual_card(ch["id"], currency="USD", initial_balance_cents=2500)
    assert card["balance_cents"] == 2500
    assert card["status"] == "active"

    loaded = issuing.load_funds(card["id"], 500)
    assert loaded["balance_cents"] == 3000

    issuing.freeze_card(card["id"])
    c2 = issuing.get_card(card["id"])
    assert c2["status"] == "frozen"

    issuing.unfreeze_card(card["id"])
    c3 = issuing.get_card(card["id"])
    assert c3["status"] == "active"

    issuing.close_card(card["id"])
    c4 = issuing.get_card(card["id"])
    assert c4["status"] == "closed"


def test_create_cardholder_validation():
    adapter = MockIssuingAdapter()
    issuing = IssuingProcessor(adapter)
    try:
        issuing.create_cardholder("")
        assert False, "should have raised"
    except PaymentError:
        pass
