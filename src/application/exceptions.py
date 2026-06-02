class ApplicationException(Exception):
    """Base exception for all application layer errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundException(ApplicationException):
    """Exception raised when a requested resource is not found."""
    pass


class BusinessRuleException(ApplicationException):
    """Exception raised when a business rule or invariant check fails in the application layer."""
    pass


class EventNotFoundException(NotFoundException):
    def __init__(self, event_id: str) -> None:
        super().__init__(f"Event with ID {event_id} was not found.")


class BookingNotFoundException(NotFoundException):
    def __init__(self, booking_id: str) -> None:
        super().__init__(f"Booking with ID {booking_id} was not found.")


class RefundNotFoundException(NotFoundException):
    def __init__(self, refund_id: str) -> None:
        super().__init__(f"Refund with ID {refund_id} was not found.")


class TicketNotFoundException(NotFoundException):
    def __init__(self, ticket_code: str) -> None:
        super().__init__(f"Ticket with code {ticket_code} was not found.")


class TicketCategoryNotFoundException(NotFoundException):
    def __init__(self, category_id: str) -> None:
        super().__init__(f"Ticket Category with ID {category_id} was not found.")
