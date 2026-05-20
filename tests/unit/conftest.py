"""Shared pytest fixtures for domain unit tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.aggregates.event import Event
from src.domain.value_objects.capacity import Capacity
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_name import EventName
from src.domain.value_objects.event_schedule import EventSchedule
from src.domain.value_objects.location import Location
from src.domain.value_objects.money import Money
from src.domain.value_objects.organizer_id import OrganizerID


def make_future_schedule(
    start_offset_days: int = 30,
    duration_days: int = 1,
) -> EventSchedule:
    now = datetime.now(tz=timezone.utc)
    start = now + timedelta(days=start_offset_days)
    end = start + timedelta(days=duration_days)
    return EventSchedule(value=DateTimeRange(start=start, end=end))


def make_event(
    name: str = "Tech Conference 2026",
    description: str = "Annual tech conference",
    capacity: int = 500,
    start_offset_days: int = 30,
) -> Event:
    return Event(
        id=EventID.generate(),
        organizer_id=OrganizerID.generate(),
        name=EventName(name),
        description=description,
        schedule=make_future_schedule(start_offset_days=start_offset_days),
        location=Location("Jakarta Convention Center"),
        capacity=Capacity(capacity),
    )


@pytest.fixture
def valid_schedule() -> EventSchedule:
    return make_future_schedule()


@pytest.fixture
def valid_event() -> Event:
    return make_event()


@pytest.fixture
def idr_price() -> Money:
    return Money(amount=Decimal("150000"), currency="IDR")
