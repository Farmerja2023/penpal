"""Small demo showing how to use the payment processor with the MockAdapter."""
from payment_processor import PaymentProcessor
from payment_processor import MockAdapter


def run_demo():
    adapter = MockAdapter()
    processor = PaymentProcessor(adapter)

    print("Charging 500 cents (USD) on fake source `tok_visa`...")
    charge = processor.charge(500, "USD", "tok_visa", "Demo charge")
    print("Charge result:", charge)

    print("Refunding the charge (full refund)...")
    ref = processor.refund(charge["id"])
    print("Refund result:", ref)


if __name__ == "__main__":
    run_demo()
