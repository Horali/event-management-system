"""DateTimeRange Value Object.

Represents a closed interval [start, end] where start <= end.
Used for both the event schedule and ticket sales periods (SalesPeriod).
Immutable: frozen dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DateTimeRange:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError(
                f"End datetime {self.end} cannot be before start datetime {self.start}"
            )

    def contains(self, dt: datetime) -> bool:
        """Return True if dt falls within [start, end]."""
        return self.start <= dt <= self.end

    def ends_before_or_at(self, dt: datetime) -> bool:
        """Return True if this range ends on or before the given datetime."""
        return self.end <= dt

    def __repr__(self) -> str:
        return f"DateTimeRange(start={self.start!r}, end={self.end!r})"


# Semantic alias used in TicketCategory context.
SalesPeriod = DateTimeRange
