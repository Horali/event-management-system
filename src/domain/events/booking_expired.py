"""BookingExpired Domain Event.

Raised when a Booking transitions to Expired after its payment deadline passes.
Carries booking_id so the application layer can release the reserved quota.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.booking_id import BookingID


@dataclass(frozen=True)
class BookingExpired(BaseDomainEvent):
    booking_id: BookingID = None  # type: ignore[assignment]
