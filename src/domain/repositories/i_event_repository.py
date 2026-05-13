"""IEventRepository — Repository Interface for the Event aggregate.

Defined in the domain layer as an abstract base class.
The infrastructure layer provides the concrete implementation.

This is the Dependency Inversion Principle in action:
- Domain declares WHAT it needs (save, find_by_id, find_all).
- Infrastructure decides HOW it's done (SQLAlchemy, psycopg, in-memory, etc.).

No imports from any infrastructure or framework library are allowed here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.aggregates.event import Event


class IEventRepository(ABC):

    @abstractmethod
    def save(self, event: Event) -> None:
        """Persist or update an Event aggregate (upsert semantics).

        The implementation must handle both insert (new event) and
        update (existing event) transparently. The application layer
        does not need to distinguish between the two cases.
        """

    @abstractmethod
    def find_by_id(self, event_id: UUID) -> Optional[Event]:
        """Return the Event with the given ID, or None if not found."""

    @abstractmethod
    def find_all(self) -> List[Event]:
        """Return all Event aggregates."""
