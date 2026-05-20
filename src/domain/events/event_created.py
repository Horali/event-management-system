from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_name import EventName
from src.domain.value_objects.organizer_id import OrganizerID


@dataclass(frozen=True)
class EventCreated(BaseDomainEvent):
    event_id: EventID = None        # type: ignore[assignment]
    organizer_id: OrganizerID = None  # type: ignore[assignment]
    name: EventName = None          # type: ignore[assignment]
