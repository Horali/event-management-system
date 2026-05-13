"""TicketCategory Entity.

Lives inside the Event aggregate boundary.
Cannot exist without an Event — never instantiated directly from outside.
All construction validation is the responsibility of Event.add_ticket_category().

is_active is mutable: it is set to False when the event is cancelled or
when the category is explicitly disabled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.money import Money

# Semantic alias: a SalesPeriod is a DateTimeRange used for ticket sales.
SalesPeriod = DateTimeRange


@dataclass
class TicketCategory:
    id: UUID
    name: str
    price: Money
    quota: int
    sales_period: SalesPeriod
    is_active: bool = field(default=True)

    def __repr__(self) -> str:
        return (
            f"TicketCategory(id={self.id!r}, name={self.name!r}, "
            f"price={self.price!r}, quota={self.quota}, "
            f"is_active={self.is_active})"
        )
