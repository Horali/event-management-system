"""Unit tests for UC2 — Publish Event.

Validate-first: negative/error cases before positive cases.
Tests cover Event.publish() and the EventPublished domain event.

Depends on UC4 (add_ticket_category) — an event needs at least one
active ticket category before it can be published.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.events.event_published import EventPublished
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.money import Money
from tests.unit.conftest import make_event
from tests.unit.test_ticket_category import make_price, make_sales_period


def add_category(event, name="Regular", quota=100, price_amount="150000"):
    """Helper: add a valid ticket category to an event."""
    event.add_ticket_category(
        name=name,
        price=make_price(price_amount),
        quota=quota,
        sales_period=make_sales_period(event),
    )
    event.collect_events()  # clear pending events after setup


class TestPublishEventValidation:
    """Negative cases — invalid publish() calls."""

    def test_publish_with_no_categories_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="no active ticket categories"):
            event.publish()

    def test_publish_cancelled_event_raises(self) -> None:
        event = make_event()
        add_category(event)
        event.publish()
        event.cancel()
        event.collect_events()
        with pytest.raises(ValueError, match="Cannot publish event with status Cancelled"):
            event.publish()

    def test_publish_already_published_raises(self) -> None:
        event = make_event()
        add_category(event)
        event.publish()
        event.collect_events()
        with pytest.raises(ValueError, match="already published"):
            event.publish()

    def test_publish_completed_event_raises(self) -> None:
        """Simulate a Completed event by directly setting status (test-only)."""
        event = make_event()
        add_category(event)
        # Force status to Completed to test the guard
        event._status = EventStatus.COMPLETED
        with pytest.raises(ValueError, match="Cannot publish event with status Completed"):
            event.publish()

    def test_publish_when_total_quota_exceeds_capacity_raises(self) -> None:
        event = make_event(capacity=100)
        add_category(event, quota=100)
        # Force a second category that pushes active quota over capacity
        from src.domain.entities.ticket_category import TicketCategory
        from src.domain.value_objects.ticket_category_id import TicketCategoryID
        extra = TicketCategory(
            id=TicketCategoryID.generate(),
            name="Extra",
            price=make_price(),
            quota=50,  # total active = 150 > 100
            sales_period=make_sales_period(event),
            is_active=True,
        )
        event._ticket_categories.append(extra)
        with pytest.raises(ValueError, match="exceeds capacity"):
            event.publish()

    def test_publish_with_only_inactive_categories_raises(self) -> None:
        event = make_event()
        cat = event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=100,
            sales_period=make_sales_period(event),
        )
        cat.is_active = False  # disable the only category
        event.collect_events()
        with pytest.raises(ValueError, match="no active ticket categories"):
            event.publish()


class TestPublishEventPositiveCases:
    """Positive cases — valid publish() calls."""

    def test_publish_transitions_to_published(self) -> None:
        event = make_event()
        add_category(event)
        event.publish()
        assert event.status == EventStatus.PUBLISHED

    def test_publish_records_event_published(self) -> None:
        event = make_event()
        add_category(event)
        event.publish()
        events = event.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], EventPublished)

    def test_event_published_carries_correct_id(self) -> None:
        event = make_event()
        add_category(event)
        event.publish()
        domain_events = event.collect_events()
        assert domain_events[0].event_id == event.id

    def test_publish_with_multiple_active_categories(self) -> None:
        event = make_event(capacity=500)
        add_category(event, name="Regular", quota=200)
        add_category(event, name="VIP", quota=100)
        event.publish()
        assert event.status == EventStatus.PUBLISHED

    def test_publish_with_quota_exactly_at_capacity(self) -> None:
        event = make_event(capacity=100)
        add_category(event, quota=100)  # exactly at capacity
        event.publish()
        assert event.status == EventStatus.PUBLISHED

    def test_status_does_not_change_on_failed_publish(self) -> None:
        event = make_event()
        # No categories — publish will fail
        with pytest.raises(ValueError):
            event.publish()
        assert event.status == EventStatus.DRAFT  # unchanged

    # Property-based: any event with valid categories and quota <= capacity
    # must transition to Published
    @settings(max_examples=100)
    @given(st.integers(min_value=1, max_value=500))
    def test_any_valid_quota_within_capacity_publishes(self, quota: int) -> None:
        event = make_event(capacity=500)
        event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=quota,
            sales_period=make_sales_period(event),
        )
        event.collect_events()
        event.publish()
        assert event.status == EventStatus.PUBLISHED
