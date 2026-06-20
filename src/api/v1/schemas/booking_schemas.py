from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal

class CreateBookingRequest(BaseModel):
    customer_id: UUID
    event_id: UUID
    ticket_category_id: UUID
    quantity: int = Field(..., gt=0)

class PayBookingRequest(BaseModel):
    payment_amount: Decimal = Field(..., gt=0)
    currency: str = "IDR"