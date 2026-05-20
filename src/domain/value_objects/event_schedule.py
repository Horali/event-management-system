"""EventSchedule Value Object.

Represents the time period during which an event takes place.
Wraps DateTimeRange to give the event schedule a meaningful domain name,
distinct from a ticket SalesPeriod which is also a DateTimeRange.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.value_objects.datetime_range import DateTimeRange


@dataclass(frozen=True)
class EventSchedule:
    value: DateTimeRange

    @staticmethod
    def of(start: datetime, end: datetime) -> EventSchedule:
        """Convenience factory — validates via DateTimeRange.__post_init__."""
        return EventSchedule(value=DateTimeRange(start=start, end=end))

    @property
    def start(self) -> datetime:
        return self.value.start

    @property
    def end(self) -> datetime:
        return self.value.end

    def __repr__(self) -> str:
        return f"EventSchedule(start={self.start!r}, end={self.end!r})"
