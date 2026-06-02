from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from src.application.exceptions import (
    BookingNotFoundException,
    BusinessRuleException,
    EventNotFoundException,
    TicketCategoryNotFoundException,
)
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.aggregates.booking import Booking
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID


@dataclass(frozen=True)
class CreateBookingCommand:
    customer_id: UUID
    event_id: UUID
    ticket_category_id: UUID
    quantity: int


class CreateBookingHandler:
    def __init__(
        self,
        event_repo: IEventRepository,
        booking_repo: IBookingRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._event_repo = event_repo
        self._booking_repo = booking_repo
        self._dispatcher = dispatcher

    def handle(self, command: CreateBookingCommand) -> str:
        # 1. Event must exist and be Published
        event_id = EventID(command.event_id)
        event = self._event_repo.find_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(command.event_id))

        if event.status != EventStatus.PUBLISHED:
            raise BusinessRuleException(
                f"Cannot create booking: Event status is {event.status.name}, must be Published"
            )

        # 2. Ticket category must exist and be active
        category_id = TicketCategoryID(command.ticket_category_id)
        category = next(
            (tc for tc in event.ticket_categories if tc.id == category_id), None
        )
        if not category:
            raise TicketCategoryNotFoundException(str(command.ticket_category_id))

        if not category.is_active:
            raise BusinessRuleException("Cannot book tickets from an inactive category")

        # 3. Within sales period
        now = datetime.now(category.sales_period.start.tzinfo or timezone.utc)
        if not category.sales_period.contains(now):
            if now < category.sales_period.start:
                raise BusinessRuleException(
                    "Ticket category sales period has not started yet"
                )
            else:
                raise BusinessRuleException("Ticket category sales period has ended")

        # 4. Quantity must not exceed remaining quota
        try:
            quantity = Quantity(command.quantity)
        except ValueError as e:
            raise BusinessRuleException(str(e))

        all_bookings = self._booking_repo.find_all()
        category_bookings = [
            b for b in all_bookings if b.ticket_category_id == category_id
        ]
        reserved_qty = sum(
            b.quantity.value
            for b in category_bookings
            if b.status in (BookingStatus.PENDING_PAYMENT, BookingStatus.PAID)
        )
        remaining_quota = category.quota - reserved_qty
        if quantity.value > remaining_quota:
            raise BusinessRuleException("Ticket quantity exceeds remaining quota")

        # 5. Customer cannot have more than one active booking for the same event
        customer_id = CustomerID(command.customer_id)
        existing_booking = self._booking_repo.find_by_customer_and_event(
            customer_id, event_id
        )
        if existing_booking and existing_booking.status in (
            BookingStatus.PENDING_PAYMENT,
            BookingStatus.PAID,
        ):
            raise BusinessRuleException(
                "Customer already has an active booking for this event"
            )

        # 6. Create booking
        try:
            booking = Booking(
                id=BookingID.generate(),
                customer_id=customer_id,
                event_id=event_id,
                ticket_category_id=category_id,
                unit_price=category.price,
                quantity=quantity,
            )
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._booking_repo.save(booking)
        self._dispatcher.dispatch_all(booking.collect_events())
        return str(booking.id.value)


@dataclass(frozen=True)
class PayBookingCommand:
    booking_id: UUID
    payment_amount: Decimal
    currency: str = "IDR"


class PayBookingHandler:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._booking_repo = booking_repo
        self._dispatcher = dispatcher

    def handle(self, command: PayBookingCommand) -> None:
        booking = self._booking_repo.find_by_id(BookingID(command.booking_id))
        if not booking:
            raise BookingNotFoundException(str(command.booking_id))

        try:
            payment_amount = Money(amount=command.payment_amount, currency=command.currency)
            booking.pay(payment_amount)
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._booking_repo.save(booking)
        self._dispatcher.dispatch_all(booking.collect_events())


@dataclass(frozen=True)
class ExpireBookingCommand:
    booking_id: UUID


class ExpireBookingHandler:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._booking_repo = booking_repo
        self._dispatcher = dispatcher

    def handle(self, command: ExpireBookingCommand) -> None:
        booking = self._booking_repo.find_by_id(BookingID(command.booking_id))
        if not booking:
            raise BookingNotFoundException(str(command.booking_id))

        try:
            booking.expire()
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._booking_repo.save(booking)
        self._dispatcher.dispatch_all(booking.collect_events())
