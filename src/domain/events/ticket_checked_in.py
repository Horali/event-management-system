"""TicketCheckedIn Domain Event.

Raised when a Ticket is successfully checked in.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.ticket_code import TicketCode


@dataclass(frozen=True)
class TicketCheckedIn(BaseDomainEvent):
    booking_id: BookingID = None  # type: ignore[assignment]
    ticket_code: TicketCode = None  # type: ignore[assignment]
