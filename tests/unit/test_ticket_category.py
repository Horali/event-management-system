"""Unit tests for UC4 — Create Ticket Category.

Validate-first: negative/error cases before positive cases.
Tests cover Event.add_ticket_category() and the TicketCategoryCreated domain event.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.aggregates.event import Event
from src.domain.events.ticket_category_created import TicketCategoryCreated
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.money import Money
from tests.unit.conftest import make_event, make_future_schedule


def make_sales_period(event: Event, days_before_start: int = 1) -> DateTimeRange:
    """Return a valid sales period that ends before the event starts."""
    sales_end = event.schedule.start - timedelta(days=days_before_start)
    sales_start = sales_end - timedelta(days=14)
    return DateTimeRange(start=sales_start, end=sales_end)

def make_price(amount: str = "150000") -> Money:
    return Money(amount=Decimal(amount), currency="IDR")


class TestAddTicketCategoryValidation:
    """Negative cases — invalid add_ticket_category() calls."""

    def test_empty_name_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="name cannot be empty"):
            event.add_ticket_category(
                name="",
                price=make_price(),
                quota=100,
                sales_period=make_sales_period(event),
            )

    def test_whitespace_only_name_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="name cannot be empty"):
            event.add_ticket_category(
                name="   ",
                price=make_price(),
                quota=100,
                sales_period=make_sales_period(event),
            )

    def test_zero_quota_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="quota must be greater than zero"):
            event.add_ticket_category(
                name="Regular",
                price=make_price(),
                quota=0,
                sales_period=make_sales_period(event),
            )

    def test_negative_quota_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="quota must be greater than zero"):
            event.add_ticket_category(
                name="Regular",
                price=make_price(),
                quota=-10,
                sales_period=make_sales_period(event),
            )

    def test_negative_price_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="cannot be negative"):
            event.add_ticket_category(
                name="Regular",
                price=Money(amount=Decimal("-1"), currency="IDR"),
                quota=100,
                sales_period=make_sales_period(event),
            )

    def test_sales_period_ends_after_event_start_raises(self) -> None:
        event = make_event()
        # Sales period ends 1 day AFTER the event starts — invalid
        bad_end = event.schedule.start + timedelta(days=1)
        bad_start = bad_end - timedelta(days=7)
        bad_period = DateTimeRange(start=bad_start, end=bad_end)
        with pytest.raises(ValueError, match="Sales period must end on or before"):
            event.add_ticket_category(
                name="Regular",
                price=make_price(),
                quota=100,
                sales_period=bad_period,
            )

    def test_sales_period_ends_exactly_on_event_start_is_valid(self) -> None:
        """Boundary: sales period ending exactly at event start is allowed."""
        event = make_event()
        exact_end = event.schedule.start
        exact_start = exact_end - timedelta(days=7)
        exact_period = DateTimeRange(start=exact_start, end=exact_end)        # Should NOT raise
        cat = event.add_ticket_category(
            name="Early Bird",
            price=make_price("50000"),
            quota=50,
            sales_period=exact_period,
        )
        assert cat is not None

    def test_quota_exceeds_capacity_raises(self) -> None:
        event = make_event(capacity=100)
        with pytest.raises(ValueError, match="would exceed event capacity"):
            event.add_ticket_category(
                name="Regular",
                price=make_price(),
                quota=101,  # 101 > 100 capacity
                sales_period=make_sales_period(event),
            )

    def test_cumulative_quota_exceeds_capacity_raises(self) -> None:
        event = make_event(capacity=100)
        # Add first category using 80 quota
        event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=80,
            sales_period=make_sales_period(event),
        )
        event.collect_events()  # clear events
        # Adding 30 more would push total to 110 > 100
        with pytest.raises(ValueError, match="would exceed event capacity"):
            event.add_ticket_category(
                name="VIP",
                price=make_price("500000"),
                quota=30,
                sales_period=make_sales_period(event),
            )

    # Property-based: any non-positive quota must be rejected
    @settings(max_examples=200)
    @given(st.integers(max_value=0))
    def test_any_non_positive_quota_raises(self, quota: int) -> None:
        event = make_event()
        with pytest.raises(ValueError):
            event.add_ticket_category(
                name="Regular",
                price=make_price(),
                quota=quota,
                sales_period=make_sales_period(event),
            )

    # Property-based: any whitespace-only name must be rejected
    @settings(max_examples=200)
    @given(st.text(alphabet=" \t\n\r", min_size=1))
    def test_any_whitespace_name_raises(self, name: str) -> None:
        event = make_event()
        with pytest.raises(ValueError):
            event.add_ticket_category(
                name=name,
                price=make_price(),
                quota=10,
                sales_period=make_sales_period(event),
            )


class TestAddTicketCategoryPositiveCases:
    """Positive cases — valid add_ticket_category() calls."""

    def test_category_added_to_event(self) -> None:
        event = make_event()
        event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=100,
            sales_period=make_sales_period(event),
        )
        assert len(event.ticket_categories) == 1

    def test_category_is_active_by_default(self) -> None:
        event = make_event()
        cat = event.add_ticket_category(
            name="VIP",
            price=make_price("500000"),
            quota=50,
            sales_period=make_sales_period(event),
        )
        assert cat.is_active is True

    def test_category_name_is_stripped(self) -> None:
        event = make_event()
        cat = event.add_ticket_category(
            name="  Early Bird  ",
            price=make_price("75000"),
            quota=30,
            sales_period=make_sales_period(event),
        )
        assert cat.name == "Early Bird"

    def test_free_ticket_price_zero_is_allowed(self) -> None:
        event = make_event()
        cat = event.add_ticket_category(
            name="Free Pass",
            price=Money(amount=Decimal("0"), currency="IDR"),
            quota=20,
            sales_period=make_sales_period(event),
        )
        assert cat.price.amount == Decimal("0")

    def test_records_ticket_category_created_event(self) -> None:
        event = make_event()
        event.collect_events()  # clear EventCreated
        cat = event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=100,
            sales_period=make_sales_period(event),
        )
        events = event.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TicketCategoryCreated)

    def test_ticket_category_created_carries_correct_ids(self) -> None:
        event = make_event()
        event.collect_events()  # clear EventCreated
        cat = event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=100,
            sales_period=make_sales_period(event),
        )
        domain_events = event.collect_events()
        tc_event = domain_events[0]
        assert isinstance(tc_event, TicketCategoryCreated)
        assert tc_event.event_id == event.id
        assert tc_event.ticket_category_id == cat.id
        assert tc_event.name == "Regular"

    def test_total_quota_updates_after_adding_category(self) -> None:
        event = make_event(capacity=500)
        event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=200,
            sales_period=make_sales_period(event),
        )
        event.add_ticket_category(
            name="VIP",
            price=make_price("500000"),
            quota=100,
            sales_period=make_sales_period(event),
        )
        assert event.total_quota == 300

    def test_multiple_categories_can_be_added_up_to_capacity(self) -> None:
        event = make_event(capacity=100)
        event.add_ticket_category(
            name="Regular", price=make_price(), quota=60,
            sales_period=make_sales_period(event),
        )
        event.add_ticket_category(
            name="VIP", price=make_price("500000"), quota=40,
            sales_period=make_sales_period(event),
        )
        assert len(event.ticket_categories) == 2
        assert event.total_quota == 100  # exactly at capacity — allowed

    def test_active_ticket_categories_returns_only_active(self) -> None:
        event = make_event(capacity=200)
        cat1 = event.add_ticket_category(
            name="Regular", price=make_price(), quota=100,
            sales_period=make_sales_period(event),
        )
        event.add_ticket_category(
            name="VIP", price=make_price("500000"), quota=50,
            sales_period=make_sales_period(event),
        )
        # Manually deactivate cat1 to simulate a disabled category
        cat1.is_active = False
        assert len(event.active_ticket_categories) == 1
        assert event.active_ticket_categories[0].name == "VIP"

    # Property-based: any valid quota within capacity must be accepted
    @settings(max_examples=100)
    @given(st.integers(min_value=1, max_value=500))
    def test_any_valid_quota_within_capacity_accepted(self, quota: int) -> None:
        event = make_event(capacity=500)
        cat = event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=quota,
            sales_period=make_sales_period(event),
        )
        assert cat.is_active is True
        assert cat.quota == quota
