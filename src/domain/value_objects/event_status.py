"""EventStatus Value Object.

Enum representing the lifecycle state of an Event.
Inherits from str so instances serialize directly to JSON strings and
compare equal to their string literals (e.g. EventStatus.DRAFT == "Draft").
"""

from enum import Enum


class EventStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
