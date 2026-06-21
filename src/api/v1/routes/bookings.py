from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import List

from src.api.dependencies import (
    get_booking_repository,
    get_create_booking_handler,
    get_pay_booking_handler,
    get_expire_booking_handler,
)
from src.infrastructure.repositories import BookingRepository
from src.api.v1.schemas.booking_schemas import CreateBookingRequest, PayBookingRequest
from src.application.commands.booking_commands import (
    CreateBookingCommand,
    CreateBookingHandler,
    PayBookingCommand,
    PayBookingHandler,
    ExpireBookingCommand,
    ExpireBookingHandler,
)
from src.application.dtos.booking_dtos import BookingDTO
from src.application.dtos.ticket_dtos import TicketDTO
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.booking_status import BookingStatus

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", status_code=201)
def create_booking(
    request: CreateBookingRequest,
    handler: CreateBookingHandler = Depends(get_create_booking_handler)
):
    command = CreateBookingCommand(
        customer_id=request.customer_id,
        event_id=request.event_id,
        ticket_category_id=request.ticket_category_id,
        quantity=request.quantity,
    )
    booking_id = handler.handle(command)
    return {"id": booking_id}

# Static route MUST be declared before /{booking_id} to avoid FastAPI
# treating "tickets" as a UUID path parameter (UC12 — View Purchased Tickets)
@router.get("/tickets", response_model=List[TicketDTO])
def get_customer_tickets(
    customer_id: UUID = Query(...),
    booking_repo: BookingRepository = Depends(get_booking_repository)
):
    all_bookings = booking_repo.find_all()
    customer_paid_bookings = [
        b for b in all_bookings
        if b.customer_id == CustomerID(customer_id) and b.status == BookingStatus.PAID
    ]

    tickets_dto = []
    for booking in customer_paid_bookings:
        for ticket in booking.tickets:
            tickets_dto.append(TicketDTO.from_domain(ticket))

    return tickets_dto

@router.get("/{booking_id}", response_model=BookingDTO)
def get_booking(
    booking_id: UUID,
    booking_repo: BookingRepository = Depends(get_booking_repository)
):
    booking = booking_repo.find_by_id(BookingID(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} was not found.")
    return BookingDTO.from_domain(booking)

@router.post("/{booking_id}/pay")
def pay_booking(
    booking_id: UUID,
    request: PayBookingRequest,
    handler: PayBookingHandler = Depends(get_pay_booking_handler)
):
    command = PayBookingCommand(
        booking_id=booking_id,
        payment_amount=request.payment_amount,
        currency=request.currency,
    )
    handler.handle(command)
    return {"message": "Booking paid successfully"}

@router.post("/{booking_id}/expire")
def expire_booking(
    booking_id: UUID,
    handler: ExpireBookingHandler = Depends(get_expire_booking_handler)
):
    command = ExpireBookingCommand(booking_id=booking_id)
    handler.handle(command)
    return {"message": "Booking expired successfully"}