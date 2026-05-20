"""TicketStatus Value Object.

Enum representing the lifecycle state of a Ticket.
Inherits from str for direct JSON serialization.
"""

from enum import Enum


class TicketStatus(str, Enum):
    ACTIVE = "Active"
    CHECKED_IN = "CheckedIn"
    CANCELLED = "Cancelled"
