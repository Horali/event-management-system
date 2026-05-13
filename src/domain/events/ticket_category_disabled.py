"""TicketCategoryDisabled Domain Event.

Raised when a TicketCategory is disabled on an Event.
Carries both IDs so the application layer can identify affected bookings.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseDomainEvent


@dataclass(frozen=True)
class TicketCategoryDisabled(BaseDomainEvent):
    event_id: UUID = None           # type: ignore[assignment]
    ticket_category_id: UUID = None  # type: ignore[assignment]
