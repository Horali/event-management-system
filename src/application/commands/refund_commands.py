from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
from src.application.exceptions import (
    BookingNotFoundException,
    BusinessRuleException,
    RefundNotFoundException,
)
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.aggregates.refund import Refund
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.repositories.i_refund_repository import IRefundRepository
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.ticket_status import TicketStatus


@dataclass(frozen=True)
class RequestRefundCommand:
    booking_id: UUID


class RequestRefundHandler:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        event_repo: IEventRepository,
        refund_repo: IRefundRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._booking_repo = booking_repo
        self._event_repo = event_repo
        self._refund_repo = refund_repo
        self._dispatcher = dispatcher

    def handle(self, command: RequestRefundCommand) -> str:
        booking_id = BookingID(command.booking_id)
        booking = self._booking_repo.find_by_id(booking_id)
        if not booking:
            raise BookingNotFoundException(str(command.booking_id))

        # 1. A refund can only be requested for a booking with the status Paid
        if booking.status != BookingStatus.PAID:
            raise BusinessRuleException(
                f"Cannot request refund for booking in status {booking.status.value}"
            )

        # 2. A refund cannot be requested if any ticket from the booking has already been checked in
        if any(t.status == TicketStatus.CHECKED_IN for t in booking.tickets):
            raise BusinessRuleException(
                "Cannot request refund: one or more tickets have already been checked in"
            )

        # 3. A refund can only be requested before the refund deadline (48 hours before event start).
        # Automatically allowed if the event is cancelled.
        event = self._event_repo.find_by_id(booking.event_id)
        if event and event.status != EventStatus.CANCELLED:
            now = datetime.now(event.schedule.start.tzinfo or timezone.utc)
            refund_deadline = event.schedule.start - timedelta(hours=48)
            if now >= refund_deadline:
                raise BusinessRuleException(
                    "Cannot request refund: refund deadline has passed (48 hours prior to event start)"
                )

        # Check if refund already exists
        existing = self._refund_repo.find_by_booking_id(booking_id)
        if existing:
            raise BusinessRuleException(
                f"Refund has already been requested for booking {command.booking_id}"
            )

        try:
            refund = Refund(
                id=RefundID.generate(),
                booking_id=booking_id,
            )
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._refund_repo.save(refund)
        self._dispatcher.dispatch_all(refund.collect_events())
        return str(refund.id.value)


@dataclass(frozen=True)
class ApproveRefundCommand:
    refund_id: UUID


class ApproveRefundHandler:
    def __init__(
        self,
        refund_repo: IRefundRepository,
        booking_repo: IBookingRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._refund_repo = refund_repo
        self._booking_repo = booking_repo
        self._dispatcher = dispatcher

    def handle(self, command: ApproveRefundCommand) -> None:
        refund = self._refund_repo.find_by_id(RefundID(command.refund_id))
        if not refund:
            raise RefundNotFoundException(str(command.refund_id))

        booking = self._booking_repo.find_by_id(refund.booking_id)
        if not booking:
            raise BookingNotFoundException(str(refund.booking_id))

        try:
            refund.approve()
            booking.refund()
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._refund_repo.save(refund)
        self._booking_repo.save(booking)

        self._dispatcher.dispatch_all(refund.collect_events())
        self._dispatcher.dispatch_all(booking.collect_events())


@dataclass(frozen=True)
class RejectRefundCommand:
    refund_id: UUID
    reason: str


class RejectRefundHandler:
    def __init__(
        self,
        refund_repo: IRefundRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._refund_repo = refund_repo
        self._dispatcher = dispatcher

    def handle(self, command: RejectRefundCommand) -> None:
        refund = self._refund_repo.find_by_id(RefundID(command.refund_id))
        if not refund:
            raise RefundNotFoundException(str(command.refund_id))

        try:
            refund.reject(command.reason)
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._refund_repo.save(refund)
        self._dispatcher.dispatch_all(refund.collect_events())


@dataclass(frozen=True)
class MarkRefundPaidOutCommand:
    refund_id: UUID
    payment_reference: str


class MarkRefundPaidOutHandler:
    def __init__(
        self,
        refund_repo: IRefundRepository,
        dispatcher: IDomainEventDispatcher,
    ) -> None:
        self._refund_repo = refund_repo
        self._dispatcher = dispatcher

    def handle(self, command: MarkRefundPaidOutCommand) -> None:
        refund = self._refund_repo.find_by_id(RefundID(command.refund_id))
        if not refund:
            raise RefundNotFoundException(str(command.refund_id))

        try:
            refund.mark_paid_out(command.payment_reference)
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._refund_repo.save(refund)
        self._dispatcher.dispatch_all(refund.collect_events())
