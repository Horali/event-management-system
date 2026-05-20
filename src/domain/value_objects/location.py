"""Location Value Object.

Represents the physical or virtual location of an Event.
Validates that the location string is non-empty and non-whitespace.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Location cannot be empty or whitespace")
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Location({self.value!r})"
