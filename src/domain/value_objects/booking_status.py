"""BookingStatus Value Object.

Enum representing the lifecycle state of a Booking.
Inherits from str for direct JSON serialization.
"""

from enum import Enum


class BookingStatus(str, Enum):
    PENDING_PAYMENT = "PendingPayment"
    PAID = "Paid"
    EXPIRED = "Expired"
    REFUNDED = "Refunded"
