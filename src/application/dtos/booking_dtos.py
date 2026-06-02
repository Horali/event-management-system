from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List
from src.application.dtos.ticket_dtos import TicketDTO
from src.domain.aggregates.booking import Booking


@dataclass(frozen=True)
class BookingDTO:
    id: str
    customer_id: str
    event_id: str
    ticket_category_id: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal
    status: str
    created_at: datetime
    payment_deadline: datetime
    tickets: List[TicketDTO]

    @classmethod
    def from_domain(cls, booking: Booking) -> "BookingDTO":
        tickets_dto = [TicketDTO.from_domain(t) for t in booking.tickets]
        return cls(
            id=str(booking.id.value),
            customer_id=str(booking.customer_id.value),
            event_id=str(booking.event_id.value),
            ticket_category_id=str(booking.ticket_category_id.value),
            unit_price=booking.unit_price.amount,
            quantity=booking.quantity.value,
            total_price=booking.total_price.amount,
            status=booking.status.name,
            created_at=booking.created_at,
            payment_deadline=booking.payment_deadline,
            tickets=tickets_dto,
        )
