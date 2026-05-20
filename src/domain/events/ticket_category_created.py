from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.ticket_category_id import TicketCategoryID


@dataclass(frozen=True)
class TicketCategoryCreated(BaseDomainEvent):
    event_id: EventID = None                    # type: ignore[assignment]
    ticket_category_id: TicketCategoryID = None  # type: ignore[assignment]
    name: str = ""
