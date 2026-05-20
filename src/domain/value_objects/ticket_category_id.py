"""TicketCategoryID Value Object.

Wraps a UUID representing the identity of a TicketCategory.
Kept separate from EventID so the two can never be accidentally swapped.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TicketCategoryID:
    value: UUID

    @staticmethod
    def generate() -> TicketCategoryID:
        """Generate a new random TicketCategoryID."""
        return TicketCategoryID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"TicketCategoryID({self.value!r})"
