from src.application.interfaces.payment_gateway import IPaymentGateway
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.money import Money

class MockPaymentGateway(IPaymentGateway):
    """Mock implementation of IPaymentGateway that approves all payments."""

    def process_payment(self, booking_id: BookingID, amount: Money) -> bool:
        print(f"[Payment Gateway] Processing payment of {amount.amount} {amount.currency} for booking {booking_id.value}")
        return True