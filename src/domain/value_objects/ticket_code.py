"""TicketCode Value Object.

A unique string code used to identify and validate a ticket at check-in.
Immutable and non-empty.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketCode:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TicketCode cannot be empty or whitespace")

    @staticmethod
    def generate() -> TicketCode:
        """Generate a unique ticket code using UUID4."""
        return TicketCode(value=str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TicketCode({self.value!r})"
