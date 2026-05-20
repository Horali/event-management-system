from __future__ import annotations
from dataclasses import dataclass
from src.domain.events.base import BaseDomainEvent
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.booking_id import BookingID


@dataclass(frozen=True)
class RefundApproved(BaseDomainEvent):
    refund_id: RefundID = None   # type: ignore[assignment]
    booking_id: BookingID = None  # type: ignore[assignment]
