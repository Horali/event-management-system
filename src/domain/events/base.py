"""Base Domain Event.

All domain events inherit from BaseDomainEvent.
Events are immutable facts — frozen dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class BaseDomainEvent:
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
