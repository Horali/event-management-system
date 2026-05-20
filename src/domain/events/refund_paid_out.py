from __future__ import annotations
from dataclasses import dataclass
from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.refund_id import RefundID


@dataclass(frozen=True)
class RefundPaidOut(BaseDomainEvent):
    refund_id: RefundID = None  # type: ignore[assignment]
    payment_reference: str = ""
