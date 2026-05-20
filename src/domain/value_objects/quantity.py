"""Quantity Value Object.

Represents the number of tickets in a booking.
Must be a positive integer (> 0).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Quantity:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(
                f"Quantity must be greater than zero, got: {self.value}"
            )

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"Quantity({self.value})"
