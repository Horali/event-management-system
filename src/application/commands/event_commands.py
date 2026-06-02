from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from src.application.exceptions import BusinessRuleException, EventNotFoundException
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.aggregates.event import Event
from src.domain.aggregates.refund import Refund
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.repositories.i_refund_repository import IRefundRepository
from src.domain.value_objects.capacity import Capacity
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_name import EventName
from src.domain.value_objects.event_schedule import EventSchedule
from src.domain.value_objects.location import Location
from src.domain.value_objects.organizer_id import OrganizerID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.refund_id import RefundID


@dataclass(frozen=True)
class CreateEventCommand:
    organizer_id: UUID
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    capacity: int


class CreateEventHandler:
    def __init__(self, event_repo: IEventRepository, dispatcher: IDomainEventDispatcher) -> None:
        self._event_repo = event_repo
        self._dispatcher = dispatcher

    def handle(self, command: CreateEventCommand) -> str:
        try:
            event_id = EventID.generate()
            organizer_id = OrganizerID(command.organizer_id)
            name = EventName(command.name)
            schedule = EventSchedule.of(command.start_date, command.end_date)
            location = Location(command.location)
            capacity = Capacity(command.capacity)

            event = Event(
                id=event_id,
                organizer_id=organizer_id,
                name=name,
                description=command.description,
                schedule=schedule,
                location=location,
                capacity=capacity,
            )
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._event_repo.save(event)
        self._dispatcher.dispatch_all(event.collect_events())
        return str(event.id.value)


@dataclass(frozen=True)
class PublishEventCommand:
    event_id: UUID


class PublishEventHandler:
    def __init__(self, event_repo: IEventRepository, dispatcher: IDomainEventDispatcher) -> None:
        self._event_repo = event_repo
        self._dispatcher = dispatcher

    def handle(self, command: PublishEventCommand) -> None:
        event = self._event_repo.find_by_id(EventID(command.event_id))
        if not event:
            raise EventNotFoundException(str(command.event_id))

        try:
            event.publish()
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._event_repo.save(event)
        self._dispatcher.dispatch_all(event.collect_events())


@dataclass(frozen=True)
class CancelEventCommand:
    event_id: UUID


class CancelEventHandler:
    def __init__(
        self,
        event_repo: IEventRepository,
        booking_repo: IBookingRepository,
        refund_repo: IRefundRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._event_repo = event_repo
        self._booking_repo = booking_repo
        self._refund_repo = refund_repo
        self._dispatcher = dispatcher

    def handle(self, command: CancelEventCommand) -> None:
        event = self._event_repo.find_by_id(EventID(command.event_id))
        if not event:
            raise EventNotFoundException(str(command.event_id))

        try:
            event.cancel()
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._event_repo.save(event)
        self._dispatcher.dispatch_all(event.collect_events())

        # Cancel related paid bookings and create refund requests
        bookings = self._booking_repo.find_all()
        event_bookings = [b for b in bookings if b.event_id == event.id]

        for booking in event_bookings:
            if booking.status == BookingStatus.PAID:
                try:
                    booking.cancel_tickets()
                    self._booking_repo.save(booking)

                    existing_refund = self._refund_repo.find_by_booking_id(booking.id)
                    if not existing_refund:
                        refund = Refund(
                            id=RefundID.generate(),
                            booking_id=booking.id,
                        )
                        self._refund_repo.save(refund)
                        self._dispatcher.dispatch_all(refund.collect_events())
                except ValueError as e:
                    # Log or handle individual booking refund failure but continue for others
                    pass
