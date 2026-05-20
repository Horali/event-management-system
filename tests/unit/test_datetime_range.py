"""Unit tests for the DateTimeRange Value Object.

Validate-first: negative/error cases before positive cases.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.domain.value_objects.datetime_range import DateTimeRange


class TestDateTimeRangeValidation:
    """Negative cases — invalid DateTimeRange construction."""

    def test_end_before_start_raises(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 5, 1, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="cannot be before"):
            DateTimeRange(start=start, end=end)

    def test_end_one_second_before_start_raises(self) -> None:
        start = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 6, 1, 11, 59, 59, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="cannot be before"):
            DateTimeRange(start=start, end=end)

    # Property-based: any (end < start) pair must be rejected
    @settings(max_examples=200)
    @given(
        st.datetimes(
            min_value=datetime(2000, 1, 1),
            max_value=datetime(9000, 1, 1),
        ),
        st.timedeltas(
            min_value=timedelta(seconds=1),
            max_value=timedelta(days=3650),
        ),
    )
    def test_any_end_before_start_raises(
        self, base: datetime, delta: timedelta
    ) -> None:
        start = base
        end = base - delta  # end is strictly before start
        with pytest.raises(ValueError):
            DateTimeRange(start=start, end=end)


class TestDateTimeRangePositiveCases:
    """Positive cases — valid DateTimeRange construction and helpers."""

    def test_equal_start_and_end_is_valid(self) -> None:
        dt = datetime(2026, 6, 1, tzinfo=timezone.utc)
        r = DateTimeRange(start=dt, end=dt)
        assert r.start == r.end

    def test_start_before_end_is_valid(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 2, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        assert r.start == start
        assert r.end == end

    def test_contains_midpoint(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 3, tzinfo=timezone.utc)
        mid = datetime(2026, 6, 2, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        assert r.contains(mid) is True

    def test_contains_start_boundary(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 3, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        assert r.contains(start) is True

    def test_contains_end_boundary(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 3, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        assert r.contains(end) is True

    def test_does_not_contain_before_start(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 3, tzinfo=timezone.utc)
        before = datetime(2026, 5, 31, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        assert r.contains(before) is False

    def test_ends_before_or_at(self) -> None:
        start = datetime(2026, 5, 1, tzinfo=timezone.utc)
        end = datetime(2026, 5, 31, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        event_start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        assert r.ends_before_or_at(event_start) is True

    def test_ends_exactly_at(self) -> None:
        dt = datetime(2026, 6, 1, tzinfo=timezone.utc)
        r = DateTimeRange(start=datetime(2026, 5, 1, tzinfo=timezone.utc), end=dt)
        assert r.ends_before_or_at(dt) is True

    def test_does_not_end_before_or_at_when_after(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 15, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        event_start = datetime(2026, 6, 10, tzinfo=timezone.utc)
        assert r.ends_before_or_at(event_start) is False

    def test_immutability(self) -> None:
        start = datetime(2026, 6, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 2, tzinfo=timezone.utc)
        r = DateTimeRange(start=start, end=end)
        with pytest.raises(Exception):
            r.start = datetime(2026, 1, 1, tzinfo=timezone.utc)  # type: ignore[misc]
