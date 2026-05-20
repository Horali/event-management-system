"""EventName Value Object.

Wraps a string representing the name of an Event.
Validates that the name is non-empty and non-whitespace at construction time.
Stored in stripped form — leading/trailing whitespace is removed silently.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Event name cannot be empty or whitespace")
        # Store stripped value
        object.__setattr__(self, "value", self.value.strip())

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"EventName({self.value!r})"
