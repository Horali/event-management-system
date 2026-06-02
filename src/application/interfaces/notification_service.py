from abc import ABC, abstractmethod
from typing import List
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.ticket_code import TicketCode


class INotificationService(ABC):
    """Interface for external notification service (Email/WhatsApp/SMS)."""

    @abstractmethod
    def send_booking_confirmation(self, email: str, booking_id: BookingID) -> None:
        """Send booking confirmation email/notification."""
        pass

    @abstractmethod
    def send_tickets(self, email: str, booking_id: BookingID, ticket_codes: List[TicketCode]) -> None:
        """Send ticket codes for check-in to customer."""
        pass

    @abstractmethod
    def send_refund_approved_notification(self, email: str, booking_id: BookingID) -> None:
        """Notify customer that their refund request has been approved."""
        pass

    @abstractmethod
    def send_refund_rejected_notification(self, email: str, booking_id: BookingID, reason: str) -> None:
        """Notify customer that their refund request has been rejected."""
        pass
