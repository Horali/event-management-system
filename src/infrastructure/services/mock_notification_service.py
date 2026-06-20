from typing import List
from src.application.interfaces.notification_service import INotificationService
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.ticket_code import TicketCode

class MockNotificationService(INotificationService):
    """Mock implementation of INotificationService that prints details to console."""

    def send_booking_confirmation(self, email: str, booking_id: BookingID) -> None:
        print(f"[Notification] Booking confirmation sent to {email} for booking {booking_id.value}")

    def send_tickets(self, email: str, booking_id: BookingID, ticket_codes: List[TicketCode]) -> None:
        codes = [c.value for c in ticket_codes]
        print(f"[Notification] Tickets {codes} sent to {email} for booking {booking_id.value}")

    def send_refund_approved_notification(self, email: str, booking_id: BookingID) -> None:
        print(f"[Notification] Refund approved notification sent to {email} for booking {booking_id.value}")

    def send_refund_rejected_notification(self, email: str, booking_id: BookingID, reason: str) -> None:
        print(f"[Notification] Refund rejected notification sent to {email} for booking {booking_id.value}. Reason: {reason}")