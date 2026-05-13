"""EventPublished Domain Event.

Raised when an Event transitions from Draft to Published.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .base import BaseDomainEvent


@dataclass(frozen=True)
class EventPublished(BaseDomainEvent):
    event_id: UUID = None  # type: ignore[assignment]
