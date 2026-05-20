"""BookingID Value Object.

Wraps a UUID representing the identity of a Booking.
Kept separate from other ID types so they can never be accidentally swapped.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class BookingID:
    value: UUID

    @staticmethod
    def generate() -> BookingID:
        return BookingID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"BookingID({self.value!r})"
