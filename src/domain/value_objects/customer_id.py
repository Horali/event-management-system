"""CustomerID Value Object.

Wraps a UUID representing the identity of a Customer.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CustomerID:
    value: UUID

    @staticmethod
    def generate() -> CustomerID:
        return CustomerID(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"CustomerID({self.value!r})"
