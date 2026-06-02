from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from src.application.exceptions import (
    BusinessRuleException,
    TicketNotFoundException,
)
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.ticket_code import TicketCode


@dataclass(frozen=True)
class CheckInTicketCommand:
    ticket_code: str
    event_id: UUID


class CheckInTicketHandler:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        event_repo: IEventRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._booking_repo = booking_repo
        self._event_repo = event_repo
        self._dispatcher = dispatcher

    def handle(self, command: CheckInTicketCommand) -> None:
        # Find booking by ticket code
        all_bookings = self._booking_repo.find_all()
        booking = next(
            (
                b
                for b in all_bookings
                for t in b.tickets
                if t.code.value == command.ticket_code
            ),
            None,
        )
        if not booking:
            raise TicketNotFoundException(command.ticket_code)

        # 1. Check-in can only be performed for the event that matches the ticket
        expected_event_id = EventID(command.event_id)
        if booking.event_id != expected_event_id:
            raise BusinessRuleException("Ticket does not match the event")

        # 2. Reject if the event has been cancelled
        event = self._event_repo.find_by_id(booking.event_id)
        if event and event.status == EventStatus.CANCELLED:
            raise BusinessRuleException("Event has been cancelled")

        # 3. Check-in day or allowed check-in window
        if event:
            now = datetime.now(event.schedule.start.tzinfo or timezone.utc)
            is_event_day = now.date() == event.schedule.start.date()
            is_within_window = event.schedule.start <= now <= event.schedule.end
            if not (is_event_day or is_within_window):
                raise BusinessRuleException(
                    "Check-in is only allowed on the event day or within the event window"
                )

        try:
            booking.check_in_ticket(TicketCode(command.ticket_code))
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._booking_repo.save(booking)
        self._dispatcher.dispatch_all(booking.collect_events())
