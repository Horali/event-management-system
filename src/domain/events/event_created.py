"""EventCreated Domain Event.

Raised when a new Event is successfully created.
Carries the minimum data needed by downstream handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseDomainEvent


@dataclass(frozen=True)
class EventCreated(BaseDomainEvent):
    event_id: UUID = None       # type: ignore[assignment]
    organizer_id: UUID = None   # type: ignore[assignment]
    name: str = ""
