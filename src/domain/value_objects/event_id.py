"""EventID Value Object.

Wraps a UUID to give the event's identity a meaningful type.
Using EventID instead of raw UUID prevents accidentally passing
an OrganizerID where an EventID is expected.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EventID:
    value: UUID

    @staticmethod
    def generate() -> EventID:
        """Generate a new random EventID."""
        return EventID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"EventID({self.value!r})"
