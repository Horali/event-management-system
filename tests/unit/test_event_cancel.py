"""Unit tests for UC3 — Cancel Event.

Validate-first: negative/error cases before positive cases.
Tests cover Event.cancel() and the EventCancelled domain event.

Depends on UC4 (add_ticket_category) and UC2 (publish) — cancellation
is only valid from Published status, so we need to be able to publish first.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.events.event_cancelled import EventCancelled
from src.domain.value_objects.event_status import EventStatus
from tests.unit.conftest import make_event
from tests.unit.test_ticket_category import make_price, make_sales_period
from tests.unit.test_event_publish import add_category


def make_published_event(capacity: int = 500):
    """Helper: return a fully published Event with one active category."""
    event = make_event(capacity=capacity)
    add_category(event, quota=min(100, capacity))
    event.publish()
    event.collect_events()  # clear EventPublished
    return event


class TestCancelEventValidation:
    """Negative cases — invalid cancel() calls."""

    def test_cancel_draft_event_raises(self) -> None:
        event = make_event()
        with pytest.raises(ValueError, match="Cannot cancel event with status Draft"):
            event.cancel()

    def test_cancel_completed_event_raises(self) -> None:
        event = make_event()
        event._status = EventStatus.COMPLETED  # force Completed for test
        with pytest.raises(ValueError, match="Cannot cancel event with status Completed"):
            event.cancel()

    def test_cancel_already_cancelled_raises(self) -> None:
        event = make_published_event()
        event.cancel()
        event.collect_events()
        with pytest.raises(ValueError, match="already cancelled"):
            event.cancel()

    # Property-based: cancelling from Draft always raises
    @settings(max_examples=50)
    @given(st.integers(min_value=1, max_value=1000))
    def test_cancel_draft_always_raises(self, capacity: int) -> None:
        event = make_event(capacity=capacity)
        with pytest.raises(ValueError):
            event.cancel()


class TestCancelEventPositiveCases:
    """Positive cases — valid cancel() calls."""

    def test_cancel_transitions_to_cancelled(self) -> None:
        event = make_published_event()
        event.cancel()
        assert event.status == EventStatus.CANCELLED

    def test_cancel_records_event_cancelled(self) -> None:
        event = make_published_event()
        event.cancel()
        events = event.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], EventCancelled)

    def test_event_cancelled_carries_correct_id(self) -> None:
        event = make_published_event()
        event.cancel()
        domain_events = event.collect_events()
        assert domain_events[0].event_id == event.id

    def test_cancel_deactivates_all_ticket_categories(self) -> None:
        event = make_event(capacity=500)
        add_category(event, name="Regular", quota=100)
        add_category(event, name="VIP", quota=50)
        add_category(event, name="Early Bird", quota=30)
        event.publish()
        event.collect_events()

        event.cancel()

        assert all(not tc.is_active for tc in event.ticket_categories)

    def test_cancel_deactivates_categories_atomically(self) -> None:
        """All categories must be inactive after cancel — none left active."""
        event = make_event(capacity=500)
        for i in range(5):
            add_category(event, name=f"Category {i}", quota=50)
        event.publish()
        event.collect_events()

        event.cancel()

        active_after = [tc for tc in event.ticket_categories if tc.is_active]
        assert active_after == []

    def test_cancel_with_no_categories_still_works(self) -> None:
        """Edge case: event published with categories, all disabled before cancel."""
        event = make_event(capacity=500)
        cat = event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=100,
            sales_period=make_sales_period(event),
        )
        event.collect_events()
        event.publish()
        event.collect_events()
        # Disable the only category manually (simulates UC5 before cancel)
        cat.is_active = False
        # Cancel should still work — status was Published
        event.cancel()
        assert event.status == EventStatus.CANCELLED

    def test_status_does_not_change_on_failed_cancel(self) -> None:
        event = make_event()  # Draft
        with pytest.raises(ValueError):
            event.cancel()
        assert event.status == EventStatus.DRAFT  # unchanged

    def test_cancelled_event_cannot_be_published(self) -> None:
        event = make_published_event()
        event.cancel()
        event.collect_events()
        with pytest.raises(ValueError, match="Cannot publish event with status Cancelled"):
            event.publish()

    # Property-based: cancelling a published event always transitions to Cancelled
    @settings(max_examples=50)
    @given(st.integers(min_value=1, max_value=500))
    def test_any_published_event_can_be_cancelled(self, quota: int) -> None:
        event = make_event(capacity=500)
        event.add_ticket_category(
            name="Regular",
            price=make_price(),
            quota=quota,
            sales_period=make_sales_period(event),
        )
        event.collect_events()
        event.publish()
        event.collect_events()
        event.cancel()
        assert event.status == EventStatus.CANCELLED
