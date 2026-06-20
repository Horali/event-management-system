from pydantic import BaseModel, Field
from uuid import UUID

class CheckInTicketRequest(BaseModel):
    ticket_code: str = Field(..., min_length=3, max_length=50)
    event_id: UUID