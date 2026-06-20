from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class CreateEventRequest(BaseModel):
    organizer_id: UUID
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field("", max_length=1000)
    start_date: datetime
    end_date: datetime
    location: str = Field(..., min_length=2, max_length=200)
    capacity: int = Field(..., gt=0)

class CreateTicketCategoryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    price: Decimal = Field(..., ge=0)
    quota: int = Field(..., gt=0)
    sales_start_date: datetime
    sales_end_date: datetime
    currency: str = "IDR"