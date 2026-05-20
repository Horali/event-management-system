from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.aggregates.event import Event
from src.domain.value_objects.event_id import EventID


class IEventRepository(ABC):

    @abstractmethod
    def save(self, event: Event) -> None:
        """Persist or update an Event aggregate (upsert semantics)."""

    @abstractmethod
    def find_by_id(self, event_id: EventID) -> Optional[Event]:
        """Return the Event with the given ID, or None if not found."""

    @abstractmethod
    def find_all(self) -> List[Event]:
        """Return all Event aggregates."""
