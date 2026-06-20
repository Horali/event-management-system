from pydantic import BaseModel, Field

class RejectRefundRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)

class MarkRefundPaidOutRequest(BaseModel):
    payment_reference: str = Field(..., min_length=3, max_length=100)