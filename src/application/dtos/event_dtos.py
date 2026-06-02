from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from src.domain.aggregates.event import Event
from src.domain.entities.ticket_category import TicketCategory


@dataclass(frozen=True)
class TicketCategoryDTO:
    id: str
    name: str
    price: Decimal
    quota: int
    sales_start_date: datetime
    sales_end_date: datetime
    is_active: bool
    status: str  # "Coming Soon", "Sales Closed", "Sold Out", "Available"
    remaining_quota: int

    @classmethod
    def from_domain(cls, category: TicketCategory, remaining_quota: int) -> "TicketCategoryDTO":
        now = datetime.now(category.sales_period.start.tzinfo or datetime.now().astimezone().tzinfo)
        
        # Determine status
        if now < category.sales_period.start:
            status = "Coming Soon"
        elif now > category.sales_period.end:
            status = "Sales Closed"
        elif remaining_quota <= 0:
            status = "Sold Out"
        else:
            status = "Available"

        return cls(
            id=str(category.id.value),
            name=category.name,
            price=category.price.amount,
            quota=category.quota,
            sales_start_date=category.sales_period.start,
            sales_end_date=category.sales_period.end,
            is_active=category.is_active,
            status=status,
            remaining_quota=remaining_quota,
        )


@dataclass(frozen=True)
class EventDTO:
    id: str
    organizer_id: str
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    capacity: int
    status: str
    lowest_price: Optional[Decimal] = None
    ticket_categories: List[TicketCategoryDTO] = None

    @classmethod
    def from_domain(
        cls, 
        event: Event, 
        remaining_quotas: Optional[dict[str, int]] = None,
        lowest_price: Optional[Decimal] = None
    ) -> "EventDTO":
        remaining_quotas = remaining_quotas or {}
        
        # Map ticket categories
        categories_dto = []
        for tc in event.ticket_categories:
            rem_quota = remaining_quotas.get(str(tc.id.value), tc.quota)
            categories_dto.append(TicketCategoryDTO.from_domain(tc, rem_quota))

        # Calculate lowest price if not provided
        if lowest_price is None and event.ticket_categories:
            active_prices = [tc.price.amount for tc in event.ticket_categories if tc.is_active]
            lowest_price = min(active_prices) if active_prices else None

        return cls(
            id=str(event.id.value),
            organizer_id=str(event.organizer_id.value),
            name=event.name.value,
            description=event.description,
            start_date=event.schedule.start,
            end_date=event.schedule.end,
            location=event.location.value,
            capacity=event.capacity.value,
            status=event.status.name,
            lowest_price=lowest_price,
            ticket_categories=categories_dto,
        )
