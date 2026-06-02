"""SQLAlchemy implementation of IRefundRepository."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from src.domain.aggregates.refund import Refund
from src.domain.repositories.i_refund_repository import IRefundRepository
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.refund_status import RefundStatus
from src.infrastructure.models.refund_model import RefundModel


class RefundRepository(IRefundRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, refund: Refund) -> None:
        existing = self._session.get(RefundModel, refund.id.value)
        if existing is None:
            self._session.add(self._to_model(refund))
        else:
            existing.status = refund.status.value
            existing.rejection_reason = refund.rejection_reason
            existing.payment_reference = refund.payment_reference
        self._session.commit()

    def find_by_id(self, refund_id: RefundID) -> Optional[Refund]:
        model = self._session.get(RefundModel, refund_id.value)
        return self._to_domain(model) if model else None

    def find_by_booking_id(self, booking_id: BookingID) -> Optional[Refund]:
        model = (
            self._session.query(RefundModel)
            .filter(RefundModel.booking_id == booking_id.value)
            .first()
        )
        return self._to_domain(model) if model else None

    def find_all(self) -> List[Refund]:
        return [self._to_domain(m) for m in self._session.query(RefundModel).all()]

    def _to_model(self, refund: Refund) -> RefundModel:
        return RefundModel(
            id=refund.id.value,
            booking_id=refund.booking_id.value,
            status=refund.status.value,
            rejection_reason=refund.rejection_reason,
            payment_reference=refund.payment_reference,
        )

    def _to_domain(self, model: RefundModel) -> Refund:
        refund = Refund.__new__(Refund)
        refund._id = RefundID(value=model.id)
        refund._booking_id = BookingID(value=model.booking_id)
        refund._status = RefundStatus(model.status)
        refund._rejection_reason = model.rejection_reason
        refund._payment_reference = model.payment_reference
        refund._pending_domain_events = []
        return refund
