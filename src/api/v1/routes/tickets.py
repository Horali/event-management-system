from fastapi import APIRouter, Depends
from src.api.dependencies import get_check_in_ticket_handler
from src.api.v1.schemas.ticket_schemas import CheckInTicketRequest
from src.application.commands.ticket_commands import CheckInTicketCommand, CheckInTicketHandler

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/check-in")
def check_in_ticket(
    request: CheckInTicketRequest,
    handler: CheckInTicketHandler = Depends(get_check_in_ticket_handler)
):
    command = CheckInTicketCommand(
        ticket_code=request.ticket_code,
        event_id=request.event_id,
    )
    handler.handle(command)
    return {"message": "Ticket checked in successfully"}