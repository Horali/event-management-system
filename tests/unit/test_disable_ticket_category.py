"""Unit tests for UC5 — Disable Ticket Category.

Validate-first: negative/error cases before positive cases.
Tests cover Event.disable_ticket_category() and the TicketCategoryDisabled domain event.

Depends on UC4 (add_ticket_category) — you need a category to disable.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.events.ticket_category_disabled import TicketCategoryDisabled
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.ticket_category_id import TicketCategoryID
from tests.unit.conftest import make_event
from tests.unit.test_ticket_category import make_price, make_sales_period
from tests.unit.test_event_publish import add_category


def add_and_get_category(event, name="Regular", quota=100):
    """Helper: add a category and return it."""
    cat = event.add_ticket_category(
        name=name,
        price=make_price(),
        quota=quota,
        sales_period=make_sales_period(event),
    )
    event.collect_events()
    return cat


class TestDisableTicketCategoryValidation:
    """Negative cases — invalid disable_ticket_category() calls."""

    def test_disable_on_completed_event_raises(self) -> None:
        event = make_event()
        cat = add_and_get_category(event)
        event._status = EventStatus.COMPLETED  # force Completed
        with pytest.raises(ValueError, match="Cannot disable ticket category on a Completed event"):
            event.disable_ticket_category(cat.id)

    def test_disable_nonexistent_category_raises(self) -> None:
        event = make_event()
        add_and_get_category(event)
        fake_id = TicketCategoryID.generate()
        with pytest.raises(ValueError, match="not found in this event"):
            event.disable_ticket_category(fake_id)

    def test_disable_already_inactive_category_raises(self) -> None:
        event = make_event()
        cat = add_and_get_category(event)
        cat.is_active = False  # already disabled
        with pytest.raises(ValueError, match="already disabled"):
            event.disable_ticket_category(cat.id)

    def test_disable_with_wrong_id_raises(self) -> None:
        event = make_event()
        add_and_get_category(event, name="Regular")
        add_and_get_category(event, name="VIP")
        with pytest.raises(ValueError, match="not found"):
            event.disable_ticket_category(TicketCategoryID.generate())


class TestDisableTicketCategoryPositiveCases:
    """Positive cases — valid disable_ticket_category() calls."""

    def test_disable_sets_is_active_false(self) -> None:
        event = make_event()
        cat = add_and_get_category(event)
        event.disable_ticket_category(cat.id)
        assert cat.is_active is False

    def test_disable_records_ticket_category_disabled_event(self) -> None:
        event = make_event()
        cat = add_and_get_category(event)
        event.disable_ticket_category(cat.id)
        events = event.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], TicketCategoryDisabled)

    def test_disabled_event_carries_correct_ids(self) -> None:
        event = make_event()
        cat = add_and_get_category(event)
        event.disable_ticket_category(cat.id)
        domain_events = event.collect_events()
        tc_event = domain_events[0]
        assert isinstance(tc_event, TicketCategoryDisabled)
        assert tc_event.event_id == event.id
        assert tc_event.ticket_category_id == cat.id

    def test_disable_on_draft_event_is_allowed(self) -> None:
        """Disabling is allowed on Draft events — only Completed is blocked."""
        event = make_event()
        cat = add_and_get_category(event)
        event.disable_ticket_category(cat.id)
        assert cat.is_active is False

    def test_disable_on_published_event_is_allowed(self) -> None:
        event = make_event(capacity=500)
        add_category(event, quota=100)
        cat2 = add_and_get_category(event, name="VIP", quota=50)
        event.publish()
        event.collect_events()
        event.disable_ticket_category(cat2.id)
        assert cat2.is_active is False

    def test_disable_on_cancelled_event_is_allowed(self) -> None:
        """Cancelled is not Completed — disable should still work."""
        event = make_event(capacity=500)
        add_category(event, quota=100)
        cat2 = add_and_get_category(event, name="VIP", quota=50)
        event.publish()
        event.collect_events()
        event.cancel()
        event.collect_events()
        # cancel() already set all to inactive, re-enable cat2 for test
        cat2.is_active = True
        event.disable_ticket_category(cat2.id)
        assert cat2.is_active is False

    def test_disable_one_category_does_not_affect_others(self) -> None:
        event = make_event(capacity=500)
        cat1 = add_and_get_category(event, name="Regular", quota=100)
        cat2 = add_and_get_category(event, name="VIP", quota=50)
        event.disable_ticket_category(cat1.id)
        assert cat1.is_active is False
        assert cat2.is_active is True  # unaffected

    def test_disable_removes_from_active_categories(self) -> None:
        event = make_event(capacity=500)
        cat1 = add_and_get_category(event, name="Regular", quota=100)
        add_and_get_category(event, name="VIP", quota=50)
        event.disable_ticket_category(cat1.id)
        active_names = [tc.name for tc in event.active_ticket_categories]
        assert "Regular" not in active_names
        assert "VIP" in active_names

    def test_disabled_category_still_in_all_categories(self) -> None:
        """Disabled categories are preserved for historical purposes."""
        event = make_event(capacity=500)
        cat = add_and_get_category(event)
        event.disable_ticket_category(cat.id)
        # Still in ticket_categories (not deleted)
        assert cat in event.ticket_categories
        # But not in active_ticket_categories
        assert cat not in event.active_ticket_categories

    def test_can_disable_multiple_categories_sequentially(self) -> None:
        event = make_event(capacity=500)
        cat1 = add_and_get_category(event, name="Regular", quota=100)
        cat2 = add_and_get_category(event, name="VIP", quota=50)
        cat3 = add_and_get_category(event, name="Early Bird", quota=30)
        event.disable_ticket_category(cat1.id)
        event.disable_ticket_category(cat2.id)
        event.disable_ticket_category(cat3.id)
        assert all(not tc.is_active for tc in event.ticket_categories)
