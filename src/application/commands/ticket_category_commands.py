from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from src.application.exceptions import (
    BusinessRuleException,
    EventNotFoundException,
    TicketCategoryNotFoundException,
)
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.repositories.i_event_repository import IEventRepository
from src.domain.value_objects.datetime_range import DateTimeRange
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.ticket_category_id import TicketCategoryID


@dataclass(frozen=True)
class CreateTicketCategoryCommand:
    event_id: UUID
    name: str
    price: Decimal
    quota: int
    sales_start_date: datetime
    sales_end_date: datetime
    currency: str = "IDR"


class CreateTicketCategoryHandler:
    def __init__(self, event_repo: IEventRepository, dispatcher: IDomainEventDispatcher) -> None:
        self._event_repo = event_repo
        self._dispatcher = dispatcher

    def handle(self, command: CreateTicketCategoryCommand) -> str:
        event = self._event_repo.find_by_id(EventID(command.event_id))
        if not event:
            raise EventNotFoundException(str(command.event_id))

        try:
            price = Money(amount=command.price, currency=command.currency)
            sales_period = DateTimeRange(
                start=command.sales_start_date, end=command.sales_end_date
            )
            ticket_category = event.add_ticket_category(
                name=command.name,
                price=price,
                quota=command.quota,
                sales_period=sales_period,
            )
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._event_repo.save(event)
        self._dispatcher.dispatch_all(event.collect_events())
        return str(ticket_category.id.value)


@dataclass(frozen=True)
class DisableTicketCategoryCommand:
    event_id: UUID
    ticket_category_id: UUID


class DisableTicketCategoryHandler:
    def __init__(self, event_repo: IEventRepository, dispatcher: IDomainEventDispatcher) -> None:
        self._event_repo = event_repo
        self._dispatcher = dispatcher

    def handle(self, command: DisableTicketCategoryCommand) -> None:
        event = self._event_repo.find_by_id(EventID(command.event_id))
        if not event:
            raise EventNotFoundException(str(command.event_id))

        # Check if category exists in event
        category_id = TicketCategoryID(command.ticket_category_id)
        category_exists = any(tc.id == category_id for tc in event.ticket_categories)
        if not category_exists:
            raise TicketCategoryNotFoundException(str(command.ticket_category_id))

        try:
            event.disable_ticket_category(category_id)
        except ValueError as e:
            raise BusinessRuleException(str(e))

        self._event_repo.save(event)
        self._dispatcher.dispatch_all(event.collect_events())
