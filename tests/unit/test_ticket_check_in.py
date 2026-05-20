"""Unit tests for UC13 — Check In Ticket.

Validate-first: negative/error cases before positive cases.
Tests cover Booking.check_in_ticket() and the TicketCheckedIn domain event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.aggregates.booking import Booking, PAYMENT_DEADLINE_MINUTES
from src.domain.events.ticket_checked_in import TicketCheckedIn
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID
from src.domain.value_objects.ticket_code import TicketCode
from src.domain.value_objects.ticket_status import TicketStatus


def make_paid_booking(quantity: int = 1) -> Booking:
    """Helper: return a Paid booking with tickets issued."""
    created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    booking = Booking(
        id=BookingID.generate(),
        customer_id=CustomerID.generate(),
        event_id=EventID.generate(),
        ticket_category_id=TicketCategoryID.generate(),
        unit_price=Money(amount=Decimal("150000"), currency="IDR"),
        quantity=Quantity(quantity),
        created_at=created,
    )
    booking.collect_events()
    within_deadline = created + timedelta(minutes=5)
    booking.pay(booking.total_price, paid_at=within_deadline)
    booking.collect_events()
    return booking


class TestCheckInTicketValidation:
    """Negative cases — invalid check_in_ticket() calls."""

    def test_already_checked_in_ticket_raises(self) -> None:
        """
        Acceptance Criteria: A ticket that has already been checked in cannot be used again.

        Implementation: check_in_ticket() checks ticket.status == CHECKED_IN first
        and raises ValueError.
        File: src/domain/aggregates/booking.py — Booking.check_in_ticket()
        """
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        booking.check_in_ticket(ticket.code)
        booking.collect_events()

        with pytest.raises(ValueError, match="already been checked in"):
            booking.check_in_ticket(ticket.code)

    def test_nonexistent_ticket_code_raises(self) -> None:
        """
        Acceptance Criteria: If the ticket code is not found, the system rejects it.

        Implementation: check_in_ticket() looks up the ticket by code.
        If not found, raises ValueError.
        """
        booking = make_paid_booking()
        fake_code = TicketCode.generate()

        with pytest.raises(ValueError, match="not found in this booking"):
            booking.check_in_ticket(fake_code)

    def test_cancelled_ticket_cannot_be_checked_in(self) -> None:
        """
        Acceptance Criteria: The ticket must have the status Active.

        Implementation: check_in_ticket() rejects any status other than Active.
        """
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        ticket.status = TicketStatus.CANCELLED  # simulate cancellation

        with pytest.raises(ValueError, match="Cannot check in ticket with status Cancelled"):
            booking.check_in_ticket(ticket.code)


class TestCheckInTicketPositiveCases:
    """Positive cases — valid check_in_ticket() calls."""

    def test_check_in_transitions_ticket_to_checked_in(self) -> None:
        """
        Acceptance Criteria: After successful check-in, the ticket status changes to CheckedIn.

        Implementation: check_in_ticket() sets ticket.status = TicketStatus.CHECKED_IN.
        File: src/domain/aggregates/booking.py — Booking.check_in_ticket()
        """
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        booking.check_in_ticket(ticket.code)
        assert ticket.status == TicketStatus.CHECKED_IN

    def test_check_in_records_ticket_checked_in_event(self) -> None:
        """
        Acceptance Criteria: After the ticket is checked in, the system raises
        the domain event TicketCheckedIn.

        Implementation: check_in_ticket() appends TicketCheckedIn to _pending_domain_events.
        Event file: src/domain/events/ticket_checked_in.py
        """
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        booking.check_in_ticket(ticket.code)

        events = booking.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TicketCheckedIn)

    def test_ticket_checked_in_carries_correct_ids(self) -> None:
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        booking.check_in_ticket(ticket.code)

        events = booking.collect_events()
        ev = events[0]
        assert isinstance(ev, TicketCheckedIn)
        assert ev.booking_id == booking.id
        assert ev.ticket_code == ticket.code

    def test_pay_issues_one_ticket_per_quantity(self) -> None:
        """
        Acceptance Criteria: After the booking is paid, the system issues tickets
        with unique ticket codes.

        Implementation: pay() creates one Ticket per quantity unit.
        """
        booking = make_paid_booking(quantity=3)
        assert len(booking.tickets) == 3

    def test_all_issued_tickets_are_active_by_default(self) -> None:
        booking = make_paid_booking(quantity=2)
        assert all(t.status == TicketStatus.ACTIVE for t in booking.tickets)

    def test_all_issued_tickets_have_unique_codes(self) -> None:
        booking = make_paid_booking(quantity=3)
        codes = [t.code for t in booking.tickets]
        assert len(set(codes)) == 3  # all unique

    def test_checking_in_one_ticket_does_not_affect_others(self) -> None:
        booking = make_paid_booking(quantity=2)
        ticket1, ticket2 = booking.tickets
        booking.check_in_ticket(ticket1.code)
        assert ticket1.status == TicketStatus.CHECKED_IN
        assert ticket2.status == TicketStatus.ACTIVE

    def test_status_unchanged_on_failed_check_in(self) -> None:
        """If check_in_ticket() raises, ticket status must remain unchanged."""
        booking = make_paid_booking()
        ticket = booking.tickets[0]
        fake_code = TicketCode.generate()

        with pytest.raises(ValueError):
            booking.check_in_ticket(fake_code)

        assert ticket.status == TicketStatus.ACTIVE
