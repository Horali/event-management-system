from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import List, Optional
from datetime import date

from src.api.dependencies import (
    get_event_repository,
    get_booking_repository,
    get_create_event_handler,
    get_publish_event_handler,
    get_cancel_event_handler,
    get_create_ticket_category_handler,
    get_disable_ticket_category_handler,
    get_sales_report_handler,
    get_event_participants_handler,
)
from src.infrastructure.repositories import EventRepository, BookingRepository
from src.api.v1.schemas.event_schemas import CreateEventRequest, CreateTicketCategoryRequest
from src.application.commands.event_commands import (
    CreateEventCommand,
    CreateEventHandler,
    PublishEventCommand,
    PublishEventHandler,
    CancelEventCommand,
    CancelEventHandler,
)
from src.application.commands.ticket_category_commands import (
    CreateTicketCategoryCommand,
    CreateTicketCategoryHandler,
    DisableTicketCategoryCommand,
    DisableTicketCategoryHandler,
)
from src.application.queries.report_queries import (
    GetSalesReportQuery,
    GetSalesReportHandler,
    GetEventParticipantsQuery,
    GetEventParticipantsHandler,
)
from src.application.dtos.event_dtos import EventDTO
from src.domain.value_objects.event_status import EventStatus
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.event_id import EventID

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", status_code=201)
def create_event(
    request: CreateEventRequest,
    handler: CreateEventHandler = Depends(get_create_event_handler)
):
    command = CreateEventCommand(
        organizer_id=request.organizer_id,
        name=request.name,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        location=request.location,
        capacity=request.capacity,
    )
    event_id = handler.handle(command)
    return {"id": event_id}

@router.post("/{event_id}/publish")
def publish_event(
    event_id: UUID,
    handler: PublishEventHandler = Depends(get_publish_event_handler)
):
    command = PublishEventCommand(event_id=event_id)
    handler.handle(command)
    return {"message": "Event published successfully"}

@router.post("/{event_id}/cancel")
def cancel_event(
    event_id: UUID,
    handler: CancelEventHandler = Depends(get_cancel_event_handler)
):
    command = CancelEventCommand(event_id=event_id)
    handler.handle(command)
    return {"message": "Event cancelled successfully"}

@router.post("/{event_id}/ticket-categories", status_code=201)
def create_ticket_category(
    event_id: UUID,
    request: CreateTicketCategoryRequest,
    handler: CreateTicketCategoryHandler = Depends(get_create_ticket_category_handler)
):
    command = CreateTicketCategoryCommand(
        event_id=event_id,
        name=request.name,
        price=request.price,
        quota=request.quota,
        sales_start_date=request.sales_start_date,
        sales_end_date=request.sales_end_date,
        currency=request.currency,
    )
    category_id = handler.handle(command)
    return {"id": category_id}

@router.patch("/{event_id}/ticket-categories/{category_id}/disable")
def disable_ticket_category(
    event_id: UUID,
    category_id: UUID,
    handler: DisableTicketCategoryHandler = Depends(get_disable_ticket_category_handler)
):
    command = DisableTicketCategoryCommand(
        event_id=event_id,
        ticket_category_id=category_id,
    )
    handler.handle(command)
    return {"message": "Ticket category disabled successfully"}

@router.get("", response_model=List[EventDTO])
def list_available_events(
    location: Optional[str] = Query(None),
    event_date: Optional[date] = Query(None),
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    events = event_repo.find_all()
    # Filter: customers can only view events with status Published
    published_events = [e for e in events if e.status == EventStatus.PUBLISHED]

    if location:
        published_events = [
            e for e in published_events if location.lower() in e.location.value.lower()
        ]
    if event_date:
        published_events = [
            e for e in published_events if e.schedule.start.date() == event_date
        ]

    all_bookings = booking_repo.find_all()

    dtos = []
    for event in published_events:
        remaining_quotas = {}
        for cat in event.ticket_categories:
            reserved_qty = sum(
                b.quantity.value
                for b in all_bookings
                if b.ticket_category_id == cat.id
                and b.status in (BookingStatus.PENDING_PAYMENT, BookingStatus.PAID)
            )
            remaining_quotas[str(cat.id.value)] = max(0, cat.quota - reserved_qty)
        
        dtos.append(EventDTO.from_domain(event, remaining_quotas=remaining_quotas))

    return dtos

@router.get("/{event_id}", response_model=EventDTO)
def get_event_detail(
    event_id: UUID,
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
):
    event = event_repo.find_by_id(EventID(event_id))
    if not event:
        raise HTTPException(status_code=404, detail=f"Event with ID {event_id} was not found.")

    all_bookings = booking_repo.find_all()
    remaining_quotas = {}
    for cat in event.ticket_categories:
        reserved_qty = sum(
            b.quantity.value
            for b in all_bookings
            if b.ticket_category_id == cat.id
            and b.status in (BookingStatus.PENDING_PAYMENT, BookingStatus.PAID)
        )
        remaining_quotas[str(cat.id.value)] = max(0, cat.quota - reserved_qty)

    return EventDTO.from_domain(event, remaining_quotas=remaining_quotas)

@router.get("/{event_id}/sales-report")
def get_sales_report(
    event_id: UUID,
    handler: GetSalesReportHandler = Depends(get_sales_report_handler)
):
    query = GetSalesReportQuery(event_id=event_id)
    return handler.handle(query)

@router.get("/{event_id}/participants")
def get_participants(
    event_id: UUID,
    handler: GetEventParticipantsHandler = Depends(get_event_participants_handler)
):
    query = GetEventParticipantsQuery(event_id=event_id)
    return handler.handle(query)