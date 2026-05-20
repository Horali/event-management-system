"""RefundID Value Object."""

from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class RefundID:
    value: UUID

    @staticmethod
    def generate() -> RefundID:
        return RefundID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"RefundID({self.value!r})"
