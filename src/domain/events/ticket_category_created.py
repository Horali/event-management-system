"""TicketCategoryCreated Domain Event.

Raised when a new TicketCategory is added to an Event.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseDomainEvent


@dataclass(frozen=True)
class TicketCategoryCreated(BaseDomainEvent):
    event_id: UUID = None           # type: ignore[assignment]
    ticket_category_id: UUID = None  # type: ignore[assignment]
    name: str = ""
