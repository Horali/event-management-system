"""SQLAlchemy implementation of IEventRepository.

Converts between the Event aggregate (domain) and EventModel (ORM).
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.aggregates.event import Event
from src.domain.entities.ticket_category import TicketCategory
from src.domain.repositories.i_event_repository import IEventRepository
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
from src.infrastructure.models.event_model import EventModel, TicketCategoryModel


class EventRepository(IEventRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, event: Event) -> None:
        existing = self._session.get(EventModel, event.id.value)
        if existing is None:
            model = self._to_model(event)
            self._session.add(model)
        else:
            self._update_model(existing, event)
        self._session.commit()

    def find_by_id(self, event_id: EventID) -> Optional[Event]:
        model = self._session.get(EventModel, event_id.value)
        if model is None:
            return None
        return self._to_domain(model)

    def find_all(self) -> List[Event]:
        models = self._session.query(EventModel).all()
        return [self._to_domain(m) for m in models]

    # ------------------------------------------------------------------ #
    # Mapping helpers                                                      #
    # ------------------------------------------------------------------ #

    def _to_model(self, event: Event) -> EventModel:
        model = EventModel(
            id=event.id.value,
            organizer_id=event.organizer_id.value,
            name=event.name.value,
            description=event.description,
            location=event.location.value,
            capacity=event.capacity.value,
            status=event.status.value,
            schedule_start=event.schedule.start,
            schedule_end=event.schedule.end,
            ticket_categories=[
                TicketCategoryModel(
                    id=tc.id.value,
                    event_id=event.id.value,
                    name=tc.name,
                    price_amount=float(tc.price.amount),
                    price_currency=tc.price.currency,
                    quota=tc.quota,
                    sales_period_start=tc.sales_period.start,
                    sales_period_end=tc.sales_period.end,
                    is_active=tc.is_active,
                )
                for tc in event.ticket_categories
            ],
        )
        return model

    def _update_model(self, model: EventModel, event: Event) -> None:
        model.name = event.name.value
        model.description = event.description
        model.location = event.location.value
        model.capacity = event.capacity.value
        model.status = event.status.value
        model.schedule_start = event.schedule.start
        model.schedule_end = event.schedule.end

        # Sync ticket categories
        existing_ids = {tc.id for tc in model.ticket_categories}
        domain_ids = {tc.id.value for tc in event.ticket_categories}

        # Remove deleted
        model.ticket_categories = [
            tc for tc in model.ticket_categories if tc.id in domain_ids
        ]

        # Update or add
        existing_map = {tc.id: tc for tc in model.ticket_categories}
        for tc in event.ticket_categories:
            if tc.id.value in existing_map:
                existing_tc = existing_map[tc.id.value]
                existing_tc.name = tc.name
                existing_tc.price_amount = float(tc.price.amount)
                existing_tc.price_currency = tc.price.currency
                existing_tc.quota = tc.quota
                existing_tc.sales_period_start = tc.sales_period.start
                existing_tc.sales_period_end = tc.sales_period.end
                existing_tc.is_active = tc.is_active
            else:
                model.ticket_categories.append(
                    TicketCategoryModel(
                        id=tc.id.value,
                        event_id=model.id,
                        name=tc.name,
                        price_amount=float(tc.price.amount),
                        price_currency=tc.price.currency,
                        quota=tc.quota,
                        sales_period_start=tc.sales_period.start,
                        sales_period_end=tc.sales_period.end,
                        is_active=tc.is_active,
                    )
                )

    def _to_domain(self, model: EventModel) -> Event:
        event = Event.__new__(Event)
        event._id = EventID(value=model.id)
        event._organizer_id = OrganizerID(value=model.organizer_id)
        event._name = EventName(model.name)
        event._description = model.description or ""
        event._schedule = EventSchedule.of(model.schedule_start, model.schedule_end)
        event._location = Location(model.location)
        event._capacity = Capacity(model.capacity)
        event._status = EventStatus(model.status)
        event._pending_domain_events = []
        event._ticket_categories = [
            self._tc_to_domain(tc) for tc in model.ticket_categories
        ]
        return event

    def _tc_to_domain(self, model: TicketCategoryModel) -> TicketCategory:
        return TicketCategory(
            id=TicketCategoryID(value=model.id),
            name=model.name,
            price=Money(amount=Decimal(str(model.price_amount)), currency=model.price_currency),
            quota=model.quota,
            sales_period=DateTimeRange(start=model.sales_period_start, end=model.sales_period_end),
            is_active=model.is_active,
        )
