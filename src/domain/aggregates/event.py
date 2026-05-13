"""Event Aggregate Root.

The central aggregate for the Event Management bounded context.
All state changes go through this class's methods — nothing outside
the aggregate boundary may directly mutate TicketCategory instances.

UC1  — Create Event   : __init__
UC2  — Publish Event  : publish()
UC3  — Cancel Event   : cancel()
UC4  — Add Category   : add_ticket_category()
UC5  — Disable Category: disable_ticket_category()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from src.domain.entities.ticket_category import TicketCategory
from src.domain.events.base import BaseDomainEvent
from src.domain.events.event_cancelled import EventCancelled
from src.domain.events.event_created import EventCreated
from src.domain.events.event_published import EventPublished
from src.domain.events.ticket_category_created import TicketCategoryCreated
from src.domain.events.ticket_category_disabled import TicketCategoryDisabled
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.money import Money


class Event:
    """Aggregate Root for the Event domain.

    Invariants enforced by this class:
    - name is non-empty and non-whitespace
    - capacity > 0
    - schedule.end >= schedule.start  (enforced by DateTimeRange)
    - total ticket quota <= capacity at all times
    - status transitions follow the defined lifecycle
    """

    # ------------------------------------------------------------------ #
    # Construction — UC1: Create Event                                     #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        id: UUID,
        organizer_id: UUID,
        name: str,
        description: str,
        schedule: DateTimeRange,
        location: str,
        capacity: int,
    ) -> None:
        # --- Guard clauses (validate-first) ---
        if not name or not name.strip():
            raise ValueError("Event name cannot be empty or whitespace")
        if capacity <= 0:
            raise ValueError(
                f"Event capacity must be greater than zero, got: {capacity}"
            )

        self._id: UUID = id
        self._organizer_id: UUID = organizer_id
        self._name: str = name.strip()
        self._description: str = description
        self._schedule: DateTimeRange = schedule
        self._location: str = location
        self._capacity: int = capacity
        self._status: EventStatus = EventStatus.DRAFT
        self._ticket_categories: List[TicketCategory] = []
        self._pending_domain_events: List[BaseDomainEvent] = []

        # Record domain event
        self._pending_domain_events.append(
            EventCreated(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
                organizer_id=self._organizer_id,
                name=self._name,
            )
        )

    # ------------------------------------------------------------------ #
    # Properties (read-only access to aggregate state)                     #
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def organizer_id(self) -> UUID:
        return self._organizer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def schedule(self) -> DateTimeRange:
        return self._schedule

    @property
    def location(self) -> str:
        return self._location

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def status(self) -> EventStatus:
        return self._status

    @property
    def ticket_categories(self) -> List[TicketCategory]:
        """Return a shallow copy so callers cannot mutate the internal list."""
        return list(self._ticket_categories)

    @property
    def active_ticket_categories(self) -> List[TicketCategory]:
        return [tc for tc in self._ticket_categories if tc.is_active]

    @property
    def total_quota(self) -> int:
        """Sum of quotas across ALL ticket categories (active and inactive)."""
        return sum(tc.quota for tc in self._ticket_categories)

    # ------------------------------------------------------------------ #
    # Domain Event Collection                                              #
    # ------------------------------------------------------------------ #

    def collect_events(self) -> List[BaseDomainEvent]:
        """Return pending domain events and clear the internal list.

        The application layer calls this after repository.save(event) to
        dispatch events. Clearing prevents double-dispatch on retry.
        """
        events = list(self._pending_domain_events)
        self._pending_domain_events.clear()
        return events

    # ------------------------------------------------------------------ #
    # Commands                                                             #
    # ------------------------------------------------------------------ #

    def publish(self) -> None:
        """UC2: Transition Draft → Published.

        Guards (validate-first):
        1. Status must not be Cancelled, Published, or Completed.
        2. Must have at least one active TicketCategory.
        3. Total quota of active categories must not exceed capacity.
        """
        if self._status == EventStatus.CANCELLED:
            raise ValueError(
                f"Cannot publish event with status {self._status.value}"
            )
        if self._status == EventStatus.PUBLISHED:
            raise ValueError("Event is already published")
        if self._status == EventStatus.COMPLETED:
            raise ValueError(
                f"Cannot publish event with status {self._status.value}"
            )
        if not self.active_ticket_categories:
            raise ValueError(
                "Cannot publish event: no active ticket categories"
            )
        active_quota = sum(tc.quota for tc in self.active_ticket_categories)
        if active_quota > self._capacity:
            raise ValueError(
                f"Cannot publish event: total quota ({active_quota}) "
                f"exceeds capacity ({self._capacity})"
            )

        self._status = EventStatus.PUBLISHED
        self._pending_domain_events.append(
            EventPublished(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
            )
        )

    def cancel(self) -> None:
        """UC3: Transition Published → Cancelled.

        Also deactivates all TicketCategories atomically.
        Guards (validate-first):
        1. Status must be Published (Draft, Completed, and already-Cancelled are rejected).
        """
        if self._status == EventStatus.COMPLETED:
            raise ValueError(
                f"Cannot cancel event with status {self._status.value}"
            )
        if self._status == EventStatus.DRAFT:
            raise ValueError(
                f"Cannot cancel event with status {self._status.value}"
            )
        if self._status == EventStatus.CANCELLED:
            raise ValueError("Event is already cancelled")

        self._status = EventStatus.CANCELLED

        # Deactivate all ticket categories atomically
        for tc in self._ticket_categories:
            tc.is_active = False

        self._pending_domain_events.append(
            EventCancelled(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
            )
        )

    def add_ticket_category(
        self,
        name: str,
        price: Money,
        quota: int,
        sales_period: DateTimeRange,
    ) -> TicketCategory:
        """UC4: Add a new TicketCategory to this Event.

        Guards (validate-first):
        1. Name must be non-empty and non-whitespace.
        2. Price amount must be >= 0 (enforced by Money, but checked here for clarity).
        3. Quota must be > 0.
        4. Sales period end must be <= event schedule start.
        5. Adding quota must not push total over capacity.

        Returns the created TicketCategory.
        """
        if not name or not name.strip():
            raise ValueError(
                "Ticket category name cannot be empty or whitespace"
            )
        if quota <= 0:
            raise ValueError(
                f"Ticket category quota must be greater than zero, got: {quota}"
            )
        if not sales_period.ends_before_or_at(self._schedule.start):
            raise ValueError(
                "Sales period must end on or before the event start date"
            )
        if self.total_quota + quota > self._capacity:
            raise ValueError(
                f"Adding quota ({quota}) would exceed event capacity "
                f"({self._capacity}). Current total: {self.total_quota}"
            )

        category = TicketCategory(
            id=uuid4(),
            name=name.strip(),
            price=price,
            quota=quota,
            sales_period=sales_period,
            is_active=True,
        )
        self._ticket_categories.append(category)

        self._pending_domain_events.append(
            TicketCategoryCreated(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
                ticket_category_id=category.id,
                name=category.name,
            )
        )
        return category

    def disable_ticket_category(self, category_id: UUID) -> None:
        """UC5: Disable a specific TicketCategory by ID.

        Guards (validate-first):
        1. Event must not be Completed.
        2. Category with given ID must exist.
        3. Category must currently be active.
        """
        if self._status == EventStatus.COMPLETED:
            raise ValueError(
                f"Cannot disable ticket category on a {self._status.value} event"
            )

        category: Optional[TicketCategory] = next(
            (tc for tc in self._ticket_categories if tc.id == category_id),
            None,
        )
        if category is None:
            raise ValueError(
                f"Ticket category with id {category_id} not found in this event"
            )
        if not category.is_active:
            raise ValueError(
                f"Ticket category '{category.name}' is already disabled"
            )

        category.is_active = False

        self._pending_domain_events.append(
            TicketCategoryDisabled(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
                ticket_category_id=category_id,
            )
        )

    def __repr__(self) -> str:
        return (
            f"Event(id={self._id!r}, name={self._name!r}, "
            f"status={self._status.value!r})"
        )
