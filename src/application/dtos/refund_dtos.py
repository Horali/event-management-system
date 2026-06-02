from dataclasses import dataclass
from typing import Optional
from src.domain.aggregates.refund import Refund


@dataclass(frozen=True)
class RefundDTO:
    id: str
    booking_id: str
    status: str
    rejection_reason: Optional[str]
    payment_reference: Optional[str]

    @classmethod
    def from_domain(cls, refund: Refund) -> "RefundDTO":
        return cls(
            id=str(refund.id.value),
            booking_id=str(refund.booking_id.value),
            status=refund.status.name,
            rejection_reason=refund.rejection_reason,
            payment_reference=refund.payment_reference,
        )
