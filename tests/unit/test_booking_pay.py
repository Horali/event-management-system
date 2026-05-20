"""Unit tests for UC10 — Pay Booking.

Validate-first: negative/error cases before positive cases.
Tests cover Booking.pay() and the BookingPaid domain event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.aggregates.booking import Booking, PAYMENT_DEADLINE_MINUTES
from src.domain.events.booking_paid import BookingPaid
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID


def make_booking(
    quantity: int = 2,
    unit_price_amount: str = "150000",
    created_at: datetime | None = None,
) -> Booking:
    return Booking(
        id=BookingID.generate(),
        customer_id=CustomerID.generate(),
        event_id=EventID.generate(),
        ticket_category_id=TicketCategoryID.generate(),
        unit_price=Money(amount=Decimal(unit_price_amount), currency="IDR"),
        quantity=Quantity(quantity),
        created_at=created_at,
    )


def total_price(booking: Booking) -> Money:
    return booking.total_price


class TestPayBookingValidation:
    """Negative cases — invalid pay() calls."""

    def test_pay_expired_booking_raises(self) -> None:
        """
        Acceptance Criteria: A booking cannot be paid if the payment deadline has passed.

        Implementation: pay() receives the current time as `paid_at`.
        If paid_at > payment_deadline, it raises ValueError.
        The deadline is set at creation time as created_at + 15 minutes.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        # Attempt to pay 1 second after the deadline
        past_deadline = created + timedelta(minutes=PAYMENT_DEADLINE_MINUTES, seconds=1)
        with pytest.raises(ValueError, match="payment deadline has passed"):
            booking.pay(total_price(booking), paid_at=past_deadline)

    def test_pay_already_paid_booking_raises(self) -> None:
        """
        Acceptance Criteria: A booking can only be paid if its status is PendingPayment.

        Implementation: pay() checks self._status == BookingStatus.PENDING_PAYMENT first.
        If status is already Paid, it raises ValueError.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        within_deadline = created + timedelta(minutes=5)
        booking.pay(total_price(booking), paid_at=within_deadline)
        booking.collect_events()

        with pytest.raises(ValueError, match="Cannot pay booking with status Paid"):
            booking.pay(total_price(booking), paid_at=within_deadline)

    def test_pay_expired_status_booking_raises(self) -> None:
        """
        Acceptance Criteria: A booking can only be paid if its status is PendingPayment.

        Implementation: If status is Expired (set by UC11), pay() raises ValueError.
        """
        booking = make_booking()
        booking.collect_events()
        booking._status = BookingStatus.EXPIRED  # simulate expiry

        with pytest.raises(ValueError, match="Cannot pay booking with status Expired"):
            booking.pay(total_price(booking))

    def test_pay_wrong_amount_raises(self) -> None:
        """
        Acceptance Criteria: The payment amount must be equal to the total booking price.

        Implementation: pay() compares payment_amount with self.total_price.
        If they differ, it raises ValueError with both amounts in the message.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(quantity=2, unit_price_amount="150000", created_at=created)
        booking.collect_events()

        wrong_amount = Money(amount=Decimal("100000"), currency="IDR")  # should be 300000
        within_deadline = created + timedelta(minutes=5)
        with pytest.raises(ValueError, match="does not match total price"):
            booking.pay(wrong_amount, paid_at=within_deadline)

    def test_pay_exactly_at_deadline_is_allowed(self) -> None:
        """Boundary: paying exactly at the deadline is valid (not after)."""
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        exactly_at_deadline = created + timedelta(minutes=PAYMENT_DEADLINE_MINUTES)
        # Should NOT raise
        booking.pay(total_price(booking), paid_at=exactly_at_deadline)
        assert booking.status == BookingStatus.PAID


class TestPayBookingPositiveCases:
    """Positive cases — valid pay() calls."""

    def test_pay_transitions_to_paid(self) -> None:
        """
        Acceptance Criteria: After payment is successful, the booking status changes to Paid.

        Implementation: pay() sets self._status = BookingStatus.PAID after all guards pass.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        within_deadline = created + timedelta(minutes=5)
        booking.pay(total_price(booking), paid_at=within_deadline)
        assert booking.status == BookingStatus.PAID

    def test_pay_records_booking_paid_event(self) -> None:
        """
        Acceptance Criteria: After the booking is paid, the system raises the domain event BookingPaid.

        Implementation: pay() appends BookingPaid to _pending_domain_events.
        """
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        within_deadline = created + timedelta(minutes=5)
        booking.pay(total_price(booking), paid_at=within_deadline)

        events = booking.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], BookingPaid)

    def test_booking_paid_carries_correct_id(self) -> None:
        created = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=created)
        booking.collect_events()

        within_deadline = created + timedelta(minutes=5)
        booking.pay(total_price(booking), paid_at=within_deadline)

        events = booking.collect_events()
        assert events[0].booking_id == booking.id

    def test_status_unchanged_on_failed_pay(self) -> None:
        """If pay() raises, status must remain PendingPayment."""
        booking = make_booking()
        booking.collect_events()

        wrong_amount = Money(amount=Decimal("1"), currency="IDR")
        with pytest.raises(ValueError):
            booking.pay(wrong_amount)

        assert booking.status == BookingStatus.PENDING_PAYMENT
