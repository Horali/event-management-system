from dataclasses import dataclass
from decimal import Decimal
from typing import List
from uuid import UUID
from src.application.dtos.report_dtos import EventSalesReportDTO, ParticipantDTO
from src.application.exceptions import EventNotFoundException
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.repositories.i_booking_repository import IBookingRepository
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.booking_status import BookingStatus


@dataclass(frozen=True)
class GetSalesReportQuery:
    event_id: UUID


class GetSalesReportHandler:
    def __init__(
        self,
        event_repo: IEventRepository,
        booking_repo: IBookingRepository,
    ) -> None:
        self._event_repo = event_repo
        self._booking_repo = booking_repo

    def handle(self, query: GetSalesReportQuery) -> EventSalesReportDTO:
        event_id = EventID(query.event_id)
        event = self._event_repo.find_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(query.event_id))

        all_bookings = self._booking_repo.find_all()
        event_bookings = [b for b in all_bookings if b.event_id == event_id]

        # 1. Number of tickets sold per category
        tickets_sold = {tc.name: 0 for tc in event.ticket_categories}
        for booking in event_bookings:
            if booking.status == BookingStatus.PAID:
                # Find category name
                category = next(
                    (tc for tc in event.ticket_categories if tc.id == booking.ticket_category_id),
                    None,
                )
                if category:
                    tickets_sold[category.name] = (
                        tickets_sold.get(category.name, 0) + booking.quantity.value
                    )

        # 2. Number of bookings by status
        bookings_by_status = {
            "PendingPayment": 0,
            "Paid": 0,
            "Expired": 0,
            "Refunded": 0,
        }
        for booking in event_bookings:
            status_name = booking.status.name
            # Map enum name or value to matching key
            if booking.status == BookingStatus.PENDING_PAYMENT:
                bookings_by_status["PendingPayment"] += 1
            elif booking.status == BookingStatus.PAID:
                bookings_by_status["Paid"] += 1
            elif booking.status == BookingStatus.EXPIRED:
                bookings_by_status["Expired"] += 1
            elif booking.status == BookingStatus.REFUNDED:
                bookings_by_status["Refunded"] += 1

        # 3. Total revenue from paid bookings
        total_revenue = sum(
            (b.total_price.amount for b in event_bookings if b.status == BookingStatus.PAID),
            Decimal("0"),
        )

        return EventSalesReportDTO(
            event_id=str(event.id.value),
            tickets_sold_per_category=tickets_sold,
            bookings_count_by_status=bookings_by_status,
            total_revenue=total_revenue,
        )


@dataclass(frozen=True)
class GetEventParticipantsQuery:
    event_id: UUID


class GetEventParticipantsHandler:
    def __init__(
        self,
        event_repo: IEventRepository,
        booking_repo: IBookingRepository,
    ) -> None:
        self._event_repo = event_repo
        self._booking_repo = booking_repo

    def handle(self, query: GetEventParticipantsQuery) -> List[ParticipantDTO]:
        event_id = EventID(query.event_id)
        event = self._event_repo.find_by_id(event_id)
        if not event:
            raise EventNotFoundException(str(query.event_id))

        all_bookings = self._booking_repo.find_all()
        # Participants list only displays customers from bookings with the status Paid.
        # Participants from refunded bookings are not displayed.
        event_paid_bookings = [
            b
            for b in all_bookings
            if b.event_id == event_id and b.status == BookingStatus.PAID
        ]

        participants = []
        for booking in event_paid_bookings:
            # Find category name
            category = next(
                (tc for tc in event.ticket_categories if tc.id == booking.ticket_category_id),
                None,
            )
            category_name = category.name if category else "Unknown"

            for ticket in booking.tickets:
                participants.append(
                    ParticipantDTO(
                        customer_id=str(booking.customer_id.value),
                        customer_name=f"Customer {str(booking.customer_id.value)[:8]}",
                        ticket_category=category_name,
                        ticket_code=ticket.code.value,
                        check_in_status=ticket.status.name,
                    )
                )

        return participants