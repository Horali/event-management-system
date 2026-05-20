"""Unit tests for UC8 — Create Ticket Booking.

Validate-first: negative/error cases before positive cases.
Tests cover Booking.__init__(), total_price (UC9), and the TicketReserved domain event.

Note: UC8 guards that require cross-aggregate checks (event is Published,
category is active, within sales period, quota not exceeded, no duplicate
active booking) are enforced by the APPLICATION layer, not the domain.
The Booking aggregate only enforces what it can see: Quantity > 0.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.aggregates.booking import Booking, PAYMENT_DEADLINE_MINUTES
from src.domain.events.ticket_reserved import TicketReserved
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
    """Helper: return a valid Booking for use in tests."""
    return Booking(
        id=BookingID.generate(),
        customer_id=CustomerID.generate(),
        event_id=EventID.generate(),
        ticket_category_id=TicketCategoryID.generate(),
        unit_price=Money(amount=Decimal(unit_price_amount), currency="IDR"),
        quantity=Quantity(quantity),
        created_at=created_at,
    )


class TestQuantityValidation:
    """Negative cases — Quantity value object validation."""

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            Quantity(0)

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="Quantity must be greater than zero"):
            Quantity(-1)

    # Property-based: any non-positive integer must be rejected
    @settings(max_examples=200)
    @given(st.integers(max_value=0))
    def test_any_non_positive_quantity_raises(self, qty: int) -> None:
        with pytest.raises(ValueError):
            Quantity(qty)


class TestBookingCreationPositiveCases:
    """Positive cases — valid Booking construction."""

    def test_new_booking_has_pending_payment_status(self) -> None:
        booking = make_booking()
        assert booking.status == BookingStatus.PENDING_PAYMENT

    def test_booking_records_ticket_reserved_event(self) -> None:
        booking = make_booking()
        events = booking.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TicketReserved)

    def test_ticket_reserved_carries_correct_ids(self) -> None:
        booking = make_booking()
        events = booking.collect_events()
        ev = events[0]
        assert isinstance(ev, TicketReserved)
        assert ev.booking_id == booking.id
        assert ev.customer_id == booking.customer_id
        assert ev.event_id == booking.event_id
        assert ev.ticket_category_id == booking.ticket_category_id
        assert ev.quantity == booking.quantity.value

    def test_collect_events_clears_list(self) -> None:
        booking = make_booking()
        booking.collect_events()
        assert booking.collect_events() == []

    def test_payment_deadline_is_15_minutes_after_creation(self) -> None:
        now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        booking = make_booking(created_at=now)
        expected_deadline = now + timedelta(minutes=PAYMENT_DEADLINE_MINUTES)
        assert booking.payment_deadline == expected_deadline

    def test_booking_stores_correct_quantity(self) -> None:
        booking = make_booking(quantity=5)
        assert booking.quantity.value == 5

    def test_booking_stores_correct_unit_price(self) -> None:
        booking = make_booking(unit_price_amount="200000")
        assert booking.unit_price.amount == Decimal("200000")

    # Property-based: any positive quantity must be accepted
    @settings(max_examples=100)
    @given(st.integers(min_value=1, max_value=1000))
    def test_any_positive_quantity_accepted(self, qty: int) -> None:
        booking = make_booking(quantity=qty)
        assert booking.status == BookingStatus.PENDING_PAYMENT
        assert booking.quantity.value == qty


class TestBookingTotalPrice:
    """UC9 — Calculate Booking Total Price."""

    def test_total_price_is_unit_price_times_quantity(self) -> None:
        booking = make_booking(quantity=3, unit_price_amount="100000")
        assert booking.total_price.amount == Decimal("300000")

    def test_total_price_for_single_ticket(self) -> None:
        booking = make_booking(quantity=1, unit_price_amount="150000")
        assert booking.total_price.amount == Decimal("150000")

    def test_total_price_for_free_ticket(self) -> None:
        booking = make_booking(quantity=5, unit_price_amount="0")
        assert booking.total_price.amount == Decimal("0")

    def test_total_price_currency_matches_unit_price(self) -> None:
        booking = make_booking(quantity=2, unit_price_amount="75000")
        assert booking.total_price.currency == "IDR"

    def test_total_price_cannot_be_negative(self) -> None:
        """Money rejects negative amounts — total price is always >= 0."""
        booking = make_booking(quantity=2, unit_price_amount="0")
        assert booking.total_price.amount >= Decimal("0")

    # Property-based: total_price == unit_price * quantity for any valid inputs
    @settings(max_examples=100)
    @given(
        st.integers(min_value=1, max_value=100),
        st.decimals(
            min_value=Decimal("0"),
            max_value=Decimal("10000000"),
            allow_nan=False,
            allow_infinity=False,
            places=0,
        ),
    )
    def test_total_price_always_equals_unit_times_quantity(
        self, qty: int, unit: Decimal
    ) -> None:
        booking = make_booking(quantity=qty, unit_price_amount=str(unit))
        assert booking.total_price.amount == unit * qty
