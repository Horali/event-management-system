"""BookingPaid Domain Event.

Raised when a Booking is successfully paid.
Carries the booking_id so downstream handlers (e.g. ticket issuance)
can identify which booking was paid.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.booking_id import BookingID


@dataclass(frozen=True)
class BookingPaid(BaseDomainEvent):
    booking_id: BookingID = None  # type: ignore[assignment]
