from abc import ABC, abstractmethod
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.money import Money


class IPaymentGateway(ABC):
    """Interface for external payment gateway integration."""

    @abstractmethod
    def process_payment(self, booking_id: BookingID, amount: Money) -> bool:
        """Process payment for a specific booking.

        Returns:
            bool: True if payment is successful, False otherwise.
        """
        pass
