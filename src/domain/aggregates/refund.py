"""Refund Aggregate Root.

Manages the refund lifecycle for a booking.

UC15 — Request Refund   : __init__
UC16 — Approve Refund   : approve()
UC17 — Reject Refund    : reject()
UC18 — Mark Paid Out    : mark_paid_out()
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from src.domain.events.base import BaseDomainEvent
from src.domain.events.refund_approved import RefundApproved
from src.domain.events.refund_paid_out import RefundPaidOut
from src.domain.events.refund_rejected import RefundRejected
from src.domain.events.refund_requested import RefundRequested
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.refund_status import RefundStatus


class Refund:
    """Aggregate Root for the Refund domain.

    Invariants enforced by this class:
    - A refund can only be approved if its status is Requested.
    - A refund can only be rejected if its status is Requested.
    - A rejection reason must be provided.
    - A refund can only be marked as paid out if its status is Approved.
    - A paid-out refund cannot be modified further.
    """

    # ------------------------------------------------------------------ #
    # Construction — UC15: Request Refund                                  #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        id: RefundID,
        booking_id: BookingID,
        requested_at: datetime | None = None,
    ) -> None:
        now = requested_at or datetime.now(tz=timezone.utc)

        self._id: RefundID = id
        self._booking_id: BookingID = booking_id
        self._status: RefundStatus = RefundStatus.REQUESTED
        self._rejection_reason: Optional[str] = None
        self._payment_reference: Optional[str] = None
        self._pending_domain_events: List[BaseDomainEvent] = []

        self._pending_domain_events.append(
            RefundRequested(
                occurred_at=now,
                refund_id=self._id,
                booking_id=self._booking_id,
            )
        )

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> RefundID:
        return self._id

    @property
    def booking_id(self) -> BookingID:
        return self._booking_id

    @property
    def status(self) -> RefundStatus:
        return self._status

    @property
    def rejection_reason(self) -> Optional[str]:
        return self._rejection_reason

    @property
    def payment_reference(self) -> Optional[str]:
        return self._payment_reference

    # ------------------------------------------------------------------ #
    # Domain Event Collection                                              #
    # ------------------------------------------------------------------ #

    def collect_events(self) -> List[BaseDomainEvent]:
        events = list(self._pending_domain_events)
        self._pending_domain_events.clear()
        return events

    # ------------------------------------------------------------------ #
    # Commands                                                             #
    # ------------------------------------------------------------------ #

    def approve(self, approved_at: datetime | None = None) -> None:
        """UC16: Transition Requested → Approved.

        Guards (validate-first):
        1. Status must be Requested.
        """
        now = approved_at or datetime.now(tz=timezone.utc)

        if self._status != RefundStatus.REQUESTED:
            raise ValueError(
                f"Cannot approve refund with status {self._status.value}"
            )

        self._status = RefundStatus.APPROVED
        self._pending_domain_events.append(
            RefundApproved(
                occurred_at=now,
                refund_id=self._id,
                booking_id=self._booking_id,
            )
        )

    def reject(self, reason: str, rejected_at: datetime | None = None) -> None:
        """UC17: Transition Requested → Rejected.

        Guards (validate-first):
        1. Status must be Requested.
        2. Rejection reason must be non-empty.
        """
        now = rejected_at or datetime.now(tz=timezone.utc)

        if self._status != RefundStatus.REQUESTED:
            raise ValueError(
                f"Cannot reject refund with status {self._status.value}"
            )
        if not reason or not reason.strip():
            raise ValueError("Rejection reason cannot be empty or whitespace")

        self._status = RefundStatus.REJECTED
        self._rejection_reason = reason.strip()
        self._pending_domain_events.append(
            RefundRejected(
                occurred_at=now,
                refund_id=self._id,
                booking_id=self._booking_id,
                reason=self._rejection_reason,
            )
        )

    def mark_paid_out(
        self,
        payment_reference: str,
        paid_out_at: datetime | None = None,
    ) -> None:
        """UC18: Transition Approved → PaidOut.

        Guards (validate-first):
        1. Status must be Approved.
        2. Payment reference must be non-empty.
        """
        now = paid_out_at or datetime.now(tz=timezone.utc)

        if self._status != RefundStatus.APPROVED:
            raise ValueError(
                f"Cannot mark refund as paid out with status {self._status.value}"
            )
        if not payment_reference or not payment_reference.strip():
            raise ValueError("Payment reference cannot be empty or whitespace")

        self._status = RefundStatus.PAID_OUT
        self._payment_reference = payment_reference.strip()
        self._pending_domain_events.append(
            RefundPaidOut(
                occurred_at=now,
                refund_id=self._id,
                payment_reference=self._payment_reference,
            )
        )

    def __repr__(self) -> str:
        return (
            f"Refund(id={self._id!r}, booking_id={self._booking_id!r}, "
            f"status={self._status.value!r})"
        )
