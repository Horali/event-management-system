"""OrganizerID Value Object.

Wraps a UUID representing the identity of an Event Organizer.
Kept separate from EventID so the two can never be accidentally swapped.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class OrganizerID:
    value: UUID

    @staticmethod
    def generate() -> OrganizerID:
        """Generate a new random OrganizerID."""
        return OrganizerID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"OrganizerID({self.value!r})"
