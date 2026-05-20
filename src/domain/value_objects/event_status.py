

from enum import Enum


class EventStatus(str, Enum):
    DRAFT = "Draft"
    PUBLISHED = "Published"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
