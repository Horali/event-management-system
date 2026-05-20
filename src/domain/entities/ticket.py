"""Ticket Entity.

Lives inside the Booking aggregate boundary.
Created when a Booking is successfully paid (UC10).
Has a unique TicketCode used for check-in validation.

is_active / status is mutable — changes on check-in or cancellation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects.ticket_code import TicketCode
from src.domain.value_objects.ticket_status import TicketStatus


@dataclass
class Ticket:
    code: TicketCode
    status: TicketStatus = field(default=TicketStatus.ACTIVE)

    def __repr__(self) -> str:
        return f"Ticket(code={self.code!r}, status={self.status.value!r})"
