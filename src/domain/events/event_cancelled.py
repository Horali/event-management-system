"""EventCancelled Domain Event.

Raised when an Event transitions to Cancelled.
Carries event_id so the application layer can find and update affected Bookings.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseDomainEvent


@dataclass(frozen=True)
class EventCancelled(BaseDomainEvent):
    event_id: UUID = None  # type: ignore[assignment]
