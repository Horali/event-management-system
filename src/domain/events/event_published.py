from __future__ import annotations

from dataclasses import dataclass

from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.event_id import EventID


@dataclass(frozen=True)
class EventPublished(BaseDomainEvent):
    event_id: EventID = None  # type: ignore[assignment]
