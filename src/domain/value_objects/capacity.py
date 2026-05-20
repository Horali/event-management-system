"""Capacity Value Object.

Represents the maximum number of attendees for an Event.
Validates that the value is a positive integer (> 0).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capacity:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(
                f"Event capacity must be greater than zero, got: {self.value}"
            )

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"Capacity({self.value})"
