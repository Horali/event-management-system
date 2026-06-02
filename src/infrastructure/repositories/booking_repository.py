"""SQLAlchemy implementation of IBookingRepository."""

from __future__ import annotations

from decimal import Decimal
from datetime import timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.aggregates.booking import Booking, PAYMENT_DEADLINE_MINUTES
from src.domain.entities.ticket import Ticket
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID
from src.domain.value_objects.ticket_code import TicketCode
from src.domain.value_objects.ticket_status import TicketStatus
from src.infrastructure.models.booking_model import BookingModel, TicketModel


class BookingRepository(IBookingRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, booking: Booking) -> None:
        existing = self._session.get(BookingModel, booking.id.value)
        if existing is None:
            model = self._to_model(booking)
            self._session.add(model)
        else:
            self._update_model(existing, booking)
        self._session.commit()

    def find_by_id(self, booking_id: BookingID) -> Optional[Booking]:
        model = self._session.get(BookingModel, booking_id.value)
        return self._to_domain(model) if model else None

    def find_by_customer_and_event(
        self, customer_id: CustomerID, event_id: EventID
    ) -> Optional[Booking]:
        model = (
            self._session.query(BookingModel)
            .filter(
                BookingModel.customer_id == customer_id.value,
                BookingModel.event_id == event_id.value,
                BookingModel.status.in_(["PendingPayment", "Paid"]),
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def find_all(self) -> List[Booking]:
        return [self._to_domain(m) for m in self._session.query(BookingModel).all()]

    def _to_model(self, booking: Booking) -> BookingModel:
        model = BookingModel(
            id=booking.id.value,
            customer_id=booking.customer_id.value,
            event_id=booking.event_id.value,
            ticket_category_id=booking.ticket_category_id.value,
            unit_price_amount=float(booking.unit_price.amount),
            unit_price_currency=booking.unit_price.currency,
            quantity=booking.quantity.value,
            status=booking.status.value,
            created_at=booking.created_at,
            payment_deadline=booking.payment_deadline,
            tickets=[
                TicketModel(
                    booking_id=booking.id.value,
                    code=t.code.value,
                    status=t.status.value,
                )
                for t in booking.tickets
            ],
        )
        return model

    def _update_model(self, model: BookingModel, booking: Booking) -> None:
        model.status = booking.status.value
        existing_codes = {t.code for t in model.tickets}
        for t in booking.tickets:
            if t.code.value in existing_codes:
                for mt in model.tickets:
                    if mt.code == t.code.value:
                        mt.status = t.status.value
            else:
                model.tickets.append(
                    TicketModel(
                        booking_id=model.id,
                        code=t.code.value,
                        status=t.status.value,
                    )
                )

    def _to_domain(self, model: BookingModel) -> Booking:
        booking = Booking.__new__(Booking)
        booking._id = BookingID(value=model.id)
        booking._customer_id = CustomerID(value=model.customer_id)
        booking._event_id = EventID(value=model.event_id)
        booking._ticket_category_id = TicketCategoryID(value=model.ticket_category_id)
        booking._unit_price = Money(
            amount=Decimal(str(model.unit_price_amount)),
            currency=model.unit_price_currency,
        )
        booking._quantity = Quantity(model.quantity)
        booking._status = BookingStatus(model.status)
        booking._created_at = model.created_at
        booking._payment_deadline = model.payment_deadline
        booking._pending_domain_events = []
        booking._tickets = [
            Ticket(code=TicketCode(t.code), status=TicketStatus(t.status))
            for t in model.tickets
        ]
        return booking
