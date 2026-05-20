"""Unit tests for UC1 — Create Event.

Validate-first: negative/error cases before positive cases.
Tests cover the Event aggregate constructor and the EventCreated domain event.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.aggregates.event import Event
from src.domain.events.event_created import EventCreated
from src.domain.value_objects.capacity import Capacity
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_name import EventName
from src.domain.value_objects.event_schedule import EventSchedule
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.location import Location
from src.domain.value_objects.organizer_id import OrganizerID
from tests.unit.conftest import make_event, make_future_schedule


class TestEventCreationValidation:
    """Negative cases — invalid Event construction."""

    def test_end_before_start_raises(self) -> None:
        start = datetime(2026, 12, 1, tzinfo=timezone.utc)
        end = datetime(2026, 11, 1, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="cannot be before"):
            DateTimeRange(start=start, end=end)

    def test_zero_capacity_raises(self) -> None:
        with pytest.raises(ValueError, match="capacity must be greater than zero"):
            make_event(capacity=0)

    def test_negative_capacity_raises(self) -> None:
        with pytest.raises(ValueError, match="capacity must be greater than zero"):
            make_event(capacity=-1)

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            make_event(name="")

    def test_whitespace_only_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            make_event(name="   ")

    def test_tab_only_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name cannot be empty"):
            make_event(name="\t\n")

    def test_empty_location_raises(self) -> None:
        with pytest.raises(ValueError, match="Location cannot be empty"):
            Event(
                id=EventID.generate(),
                organizer_id=OrganizerID.generate(),
                name=EventName("Valid Name"),
                description="desc",
                schedule=make_future_schedule(),
                location=Location("   "),  # whitespace only
                capacity=Capacity(100),
            )

    # Property-based: any non-positive capacity must be rejected
    @settings(max_examples=200)
    @given(st.integers(max_value=0))
    def test_any_non_positive_capacity_raises(self, capacity: int) -> None:
        with pytest.raises(ValueError):
            Capacity(capacity)

    # Property-based: any whitespace-only string must be rejected as name
    @settings(max_examples=200)
    @given(st.text(alphabet=" \t\n\r", min_size=1))
    def test_any_whitespace_name_raises(self, name: str) -> None:
        with pytest.raises(ValueError):
            EventName(name)


class TestEventCreationPositiveCases:
    """Positive cases — valid Event construction."""

    def test_valid_event_has_draft_status(self) -> None:
        event = make_event()
        assert event.status == EventStatus.DRAFT

    def test_valid_event_records_event_created(self) -> None:
        event = make_event()
        events = event.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], EventCreated)

    def test_event_created_carries_correct_id(self) -> None:
        event = make_event()
        domain_events = event.collect_events()
        created_event = domain_events[0]
        assert isinstance(created_event, EventCreated)
        assert created_event.event_id == event.id

    def test_collect_events_clears_list(self) -> None:
        event = make_event()
        event.collect_events()
        second_call = event.collect_events()
        assert second_call == []

    def test_event_name_is_stripped(self) -> None:
        event = make_event(name="  My Event  ")
        assert event.name.value == "My Event"

    def test_event_has_no_ticket_categories_initially(self) -> None:
        event = make_event()
        assert event.ticket_categories == []

    def test_event_total_quota_is_zero_initially(self) -> None:
        event = make_event()
        assert event.total_quota == 0

    # Property-based: any valid event must have DRAFT status
    @settings(max_examples=100)
    @given(
        st.text(min_size=1).filter(lambda s: s.strip() != ""),
        st.integers(min_value=1, max_value=100_000),
    )
    def test_any_valid_event_has_draft_status(self, name: str, capacity: int) -> None:
        event = Event(
            id=EventID.generate(),
            organizer_id=OrganizerID.generate(),
            name=EventName(name),
            description="",
            schedule=make_future_schedule(),
            location=Location("Jakarta"),
            capacity=Capacity(capacity),
        )
        assert event.status == EventStatus.DRAFT
