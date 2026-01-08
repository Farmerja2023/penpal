"""Demo for virtual prepaid card issuing using the MockIssuingAdapter."""
from payment_processor import IssuingProcessor, MockIssuingAdapter


def run_demo():
    adapter = MockIssuingAdapter()
    issuing = IssuingProcessor(adapter)

    print("Creating cardholder Alice...")
    ch = issuing.create_cardholder("Alice Example", email="alice@example.com")
    print("Cardholder:", ch)

    print("Issuing virtual card with $10.00 initial balance...")
    card = issuing.issue_virtual_card(ch["id"], currency="USD", initial_balance_cents=1000)
    print("Card:", card)

    print("Loading $5.00 onto card...")
    loaded = issuing.load_funds(card["id"], 500)
    print("Loaded:", loaded)

    print("Freezing card...")
    print(issuing.freeze_card(card["id"]))

    print("Unfreezing card...")
    print(issuing.unfreeze_card(card["id"]))

    print("Closing card...")
    print(issuing.close_card(card["id"]))


if __name__ == "__main__":
    run_demo()
