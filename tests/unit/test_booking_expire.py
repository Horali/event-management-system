"""Unit tests for UC11 — Expire Booking.

Validate-first: negative/error cases before positive cases.
Tests cover Booking.expire() and the BookingExpired domain event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.aggregates.booking import Booking, PAYMENT_DEADLINE_MINUTES
from src.domain.events.booking_expired import BookingExpired
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID


def make_booking(created_at: datetime | None = None) -> Booking:
    return Booking(
        id=BookingID.generate(),
        customer_id=CustomerID.generate(),
        event_id=EventID.generate(),
        ticket_category_id=TicketCategoryID.generate(),
        unit_price=Money(amount=Decimal("150000"), currency="IDR"),
        quantity=Quantity(2),
        created_at=created_at,
    )


class TestExpireBookingValidation:
    """Negative cases — invalid expire() calls."""

    def test_paid_booking_cannot_expire(self) -> None:
        """
        Acceptance Criteria: A booking with the status Paid cannot be marked as expired.

        Implementation: expire() checks if status is Paid first and raises ValueError.
        File: src/domain/aggregates/booking.py — Booking.expire(), first guard.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        # Pay the booking first
        within_deadline = created + timedelta(minutes=5)
        booking.pay(booking.total_price, paid_at=within_deadline)
        booking.collect_events()

        # Now try to expire it — should fail
        with pytest.raises(ValueError, match="already been paid"):
            booking.expire()

    def test_already_expired_booking_cannot_expire_again(self) -> None:
        """
        Acceptance Criteria: Only PendingPayment bookings can expire.

        Implementation: expire() rejects any status other than PendingPayment.
        """
        booking = make_booking()
        booking.collect_events()
        booking.expire()
        booking.collect_events()

        with pytest.raises(ValueError, match="Cannot expire booking with status Expired"):
            booking.expire()


class TestExpireBookingPositiveCases:
    """Positive cases — valid expire() calls."""

    def test_expire_transitions_to_expired(self) -> None:
        """
        Acceptance Criteria: A booking with the status PendingPayment changes to
        Expired after its payment deadline has passed.

        Implementation: expire() sets self._status = BookingStatus.EXPIRED.
        File: src/domain/aggregates/booking.py — Booking.expire(), after guards.
        """
        booking = make_booking()
        booking.collect_events()
        booking.expire()
        assert booking.status == BookingStatus.EXPIRED

    def test_expire_records_booking_expired_event(self) -> None:
        """
        Acceptance Criteria: After a booking expires, the system raises the
        domain event BookingExpired.

        Implementation: expire() appends BookingExpired to _pending_domain_events.
        File: src/domain/aggregates/booking.py — Booking.expire(), last lines.
        Event class: src/domain/events/booking_expired.py
        """
        booking = make_booking()
        booking.collect_events()
        booking.expire()

        events = booking.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], BookingExpired)

    def test_booking_expired_carries_correct_id(self) -> None:
        booking = make_booking()
        booking.collect_events()
        booking.expire()

        events = booking.collect_events()
        assert events[0].booking_id == booking.id

    def test_status_unchanged_on_failed_expire(self) -> None:
        """If expire() raises, status must remain unchanged."""
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        # Pay it first
        booking.pay(booking.total_price, paid_at=created + timedelta(minutes=5))
        booking.collect_events()

        # Try to expire — fails, status stays Paid
        with pytest.raises(ValueError):
            booking.expire()
        assert booking.status == BookingStatus.PAID
