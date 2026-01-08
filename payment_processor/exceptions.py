class PaymentError(Exception):
    """Generic payment processing error."""


class AdapterError(PaymentError):
    """Raised when a payment adapter fails."""
