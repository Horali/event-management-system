"""TicketReserved Domain Event.

Raised when a new Booking is successfully created.
Carries enough data for downstream handlers to identify the reservation.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.ticket_category_id import TicketCategoryID


@dataclass(frozen=True)
class TicketReserved(BaseDomainEvent):
    booking_id: BookingID = None            # type: ignore[assignment]
    customer_id: CustomerID = None          # type: ignore[assignment]
    event_id: EventID = None                # type: ignore[assignment]
    ticket_category_id: TicketCategoryID = None  # type: ignore[assignment]
    quantity: int = 0
