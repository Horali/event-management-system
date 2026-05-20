"""Event Aggregate Root.

The central aggregate for the Event Management bounded context.
All state changes go through this class's methods — nothing outside
the aggregate boundary may directly mutate TicketCategory instances.

UC1  — Create Event        : __init__
UC2  — Publish Event       : publish()
UC3  — Cancel Event        : cancel()
UC4  — Add Category        : add_ticket_category()
UC5  — Disable Category    : disable_ticket_category()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from src.domain.entities.ticket_category import TicketCategory
from src.domain.events.base import BaseDomainEvent
from src.domain.events.event_cancelled import EventCancelled
from src.domain.events.event_created import EventCreated
from src.domain.events.event_published import EventPublished
from src.domain.events.ticket_category_created import TicketCategoryCreated
from src.domain.events.ticket_category_disabled import TicketCategoryDisabled
from src.domain.value_objects.capacity import Capacity
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.event_name import EventName
from src.domain.value_objects.event_schedule import EventSchedule
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.location import Location
from src.domain.value_objects.money import Money
from src.domain.value_objects.organizer_id import OrganizerID
from src.domain.value_objects.ticket_category_id import TicketCategoryID


class Event:
    """Aggregate Root for the Event domain.

    Invariants enforced by this class:
    - name is non-empty and non-whitespace       (enforced by EventName)
    - capacity > 0                               (enforced by Capacity)
    - schedule.end >= schedule.start             (enforced by EventSchedule → DateTimeRange)
    - location is non-empty                      (enforced by Location)
    - total ticket quota <= capacity at all times
    - status transitions follow the defined lifecycle
    """

    # ------------------------------------------------------------------ #
    # Construction — UC1: Create Event                                     #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        id: EventID,
        organizer_id: OrganizerID,
        name: EventName,
        description: str,
        schedule: EventSchedule,
        location: Location,
        capacity: Capacity,
    ) -> None:
        self._id: EventID = id
        self._organizer_id: OrganizerID = organizer_id
        self._name: EventName = name
        self._description: str = description
        self._schedule: EventSchedule = schedule
        self._location: Location = location
        self._capacity: Capacity = capacity
        self._status: EventStatus = EventStatus.DRAFT
        self._ticket_categories: List[TicketCategory] = []
        self._pending_domain_events: List[BaseDomainEvent] = []

        self._pending_domain_events.append(
            EventCreated(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
                organizer_id=self._organizer_id,
                name=self._name,
            )
        )

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> EventID:
        return self._id

    @property
    def organizer_id(self) -> OrganizerID:
        return self._organizer_id

    @property
    def name(self) -> EventName:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def schedule(self) -> EventSchedule:
        return self._schedule

    @property
    def location(self) -> Location:
        return self._location

    @property
    def capacity(self) -> Capacity:
        return self._capacity

    @property
    def status(self) -> EventStatus:
        return self._status

    @property
    def ticket_categories(self) -> List[TicketCategory]:
        return list(self._ticket_categories)

    @property
    def active_ticket_categories(self) -> List[TicketCategory]:
        return [tc for tc in self._ticket_categories if tc.is_active]

    @property
    def total_quota(self) -> int:
        return sum(tc.quota for tc in self._ticket_categories)

    # ------------------------------------------------------------------ #
    # Domain Event Collection                                              #
    # ------------------------------------------------------------------ #

    def collect_events(self) -> List[BaseDomainEvent]:
        events = list(self._pending_domain_events)
        self._pending_domain_events.clear()
        return events

    # ------------------------------------------------------------------ #
    # Commands                                                             #
    # ------------------------------------------------------------------ #

    def publish(self) -> None:
        """UC2: Transition Draft → Published."""
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
        if active_quota > self._capacity.value:
            raise ValueError(
                f"Cannot publish event: total quota ({active_quota}) "
                f"exceeds capacity ({self._capacity.value})"
            )

        self._status = EventStatus.PUBLISHED
        self._pending_domain_events.append(
            EventPublished(
                occurred_at=datetime.now(tz=timezone.utc),
                event_id=self._id,
            )
        )

    def cancel(self) -> None:
        """UC3: Transition Published → Cancelled. Deactivates all categories."""
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
        """UC4: Add a new TicketCategory to this Event."""
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
        if self.total_quota + quota > self._capacity.value:
            raise ValueError(
                f"Adding quota ({quota}) would exceed event capacity "
                f"({self._capacity.value}). Current total: {self.total_quota}"
            )

        category_id = TicketCategoryID.generate()
        category = TicketCategory(
            id=category_id,
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
                ticket_category_id=category_id,
                name=category.name,
            )
        )
        return category

    def disable_ticket_category(self, category_id: TicketCategoryID) -> None:
        """UC5: Disable a specific TicketCategory by ID."""
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
