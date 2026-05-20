"""Unit tests for UC15-UC18 — Refund lifecycle.

UC15: Request Refund   — Refund.__init__()
UC16: Approve Refund   — Refund.approve()
UC17: Reject Refund    — Refund.reject()
UC18: Mark Paid Out    — Refund.mark_paid_out()

Validate-first: negative/error cases before positive cases.
"""

from __future__ import annotations

import pytest

from src.domain.aggregates.refund import Refund
from src.domain.events.refund_approved import RefundApproved
from src.domain.events.refund_paid_out import RefundPaidOut
from src.domain.events.refund_rejected import RefundRejected
from src.domain.events.refund_requested import RefundRequested
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.refund_status import RefundStatus


def make_refund() -> Refund:
    return Refund(id=RefundID.generate(), booking_id=BookingID.generate())


def make_approved_refund() -> Refund:
    refund = make_refund()
    refund.collect_events()
    refund.approve()
    refund.collect_events()
    return refund


# ------------------------------------------------------------------ #
# UC15 — Request Refund                                               #
# ------------------------------------------------------------------ #

class TestRequestRefund:
    def test_new_refund_has_requested_status(self) -> None:
        refund = make_refund()
        assert refund.status == RefundStatus.REQUESTED

    def test_new_refund_records_refund_requested_event(self) -> None:
        refund = make_refund()
        events = refund.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], RefundRequested)

    def test_refund_requested_carries_correct_ids(self) -> None:
        refund = make_refund()
        events = refund.collect_events()
        ev = events[0]
        assert ev.refund_id == refund.id
        assert ev.booking_id == refund.booking_id


# ------------------------------------------------------------------ #
# UC16 — Approve Refund                                               #
# ------------------------------------------------------------------ #

class TestApproveRefund:
    def test_approve_non_requested_refund_raises(self) -> None:
        """Criteria: A refund can only be approved if its status is Requested."""
        refund = make_refund()
        refund.collect_events()
        refund.approve()
        refund.collect_events()
        with pytest.raises(ValueError, match="Cannot approve refund with status Approved"):
            refund.approve()

    def test_approve_rejected_refund_raises(self) -> None:
        refund = make_refund()
        refund.collect_events()
        refund.reject("invalid request")
        refund.collect_events()
        with pytest.raises(ValueError, match="Cannot approve refund with status Rejected"):
            refund.approve()

    def test_approve_transitions_to_approved(self) -> None:
        """Criteria: When a refund is approved, its status changes to Approved."""
        refund = make_refund()
        refund.collect_events()
        refund.approve()
        assert refund.status == RefundStatus.APPROVED

    def test_approve_records_refund_approved_event(self) -> None:
        """Criteria: After a refund is approved, the system raises RefundApproved."""
        refund = make_refund()
        refund.collect_events()
        refund.approve()
        events = refund.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], RefundApproved)

    def test_refund_approved_carries_correct_ids(self) -> None:
        refund = make_refund()
        refund.collect_events()
        refund.approve()
        events = refund.collect_events()
        assert events[0].refund_id == refund.id
        assert events[0].booking_id == refund.booking_id


# ------------------------------------------------------------------ #
# UC17 — Reject Refund                                                #
# ------------------------------------------------------------------ #

class TestRejectRefund:
    def test_reject_non_requested_refund_raises(self) -> None:
        """Criteria: A refund can only be rejected if its status is Requested."""
        refund = make_approved_refund()
        with pytest.raises(ValueError, match="Cannot reject refund with status Approved"):
            refund.reject("reason")

    def test_reject_without_reason_raises(self) -> None:
        """Criteria: A rejection reason must be provided."""
        refund = make_refund()
        refund.collect_events()
        with pytest.raises(ValueError, match="Rejection reason cannot be empty"):
            refund.reject("")

    def test_reject_whitespace_reason_raises(self) -> None:
        """Criteria: A rejection reason must be provided (not just whitespace)."""
        refund = make_refund()
        refund.collect_events()
        with pytest.raises(ValueError, match="Rejection reason cannot be empty"):
            refund.reject("   ")

    def test_reject_transitions_to_rejected(self) -> None:
        """Criteria: When a refund is rejected, its status changes to Rejected."""
        refund = make_refund()
        refund.collect_events()
        refund.reject("Customer already attended")
        assert refund.status == RefundStatus.REJECTED

    def test_reject_stores_reason(self) -> None:
        refund = make_refund()
        refund.collect_events()
        refund.reject("  No valid reason  ")
        assert refund.rejection_reason == "No valid reason"

    def test_reject_records_refund_rejected_event(self) -> None:
        """Criteria: After a refund is rejected, the system raises RefundRejected."""
        refund = make_refund()
        refund.collect_events()
        refund.reject("Not eligible")
        events = refund.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], RefundRejected)

    def test_refund_rejected_carries_reason(self) -> None:
        refund = make_refund()
        refund.collect_events()
        refund.reject("Not eligible")
        events = refund.collect_events()
        assert events[0].reason == "Not eligible"


# ------------------------------------------------------------------ #
# UC18 — Mark Refund as Paid Out                                      #
# ------------------------------------------------------------------ #

class TestMarkRefundPaidOut:
    def test_mark_paid_out_non_approved_raises(self) -> None:
        """Criteria: A refund can only be marked as paid out if its status is Approved."""
        refund = make_refund()
        refund.collect_events()
        with pytest.raises(ValueError, match="Cannot mark refund as paid out with status Requested"):
            refund.mark_paid_out("REF-001")

    def test_mark_paid_out_without_reference_raises(self) -> None:
        """Criteria: A payment reference must be recorded."""
        refund = make_approved_refund()
        with pytest.raises(ValueError, match="Payment reference cannot be empty"):
            refund.mark_paid_out("")

    def test_mark_paid_out_transitions_to_paid_out(self) -> None:
        """Criteria: When the refund is paid out, its status changes to PaidOut."""
        refund = make_approved_refund()
        refund.mark_paid_out("REF-2026-001")
        assert refund.status == RefundStatus.PAID_OUT

    def test_mark_paid_out_stores_reference(self) -> None:
        """Criteria: A payment reference must be recorded."""
        refund = make_approved_refund()
        refund.mark_paid_out("  REF-2026-001  ")
        assert refund.payment_reference == "REF-2026-001"

    def test_mark_paid_out_records_refund_paid_out_event(self) -> None:
        """Criteria: After the refund is paid out, the system raises RefundPaidOut."""
        refund = make_approved_refund()
        refund.mark_paid_out("REF-2026-001")
        events = refund.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], RefundPaidOut)

    def test_paid_out_refund_cannot_be_approved_again(self) -> None:
        """Criteria: A paid-out refund cannot be approved, rejected, or cancelled again."""
        refund = make_approved_refund()
        refund.mark_paid_out("REF-001")
        refund.collect_events()
        with pytest.raises(ValueError):
            refund.approve()

    def test_paid_out_refund_cannot_be_rejected(self) -> None:
        refund = make_approved_refund()
        refund.mark_paid_out("REF-001")
        refund.collect_events()
        with pytest.raises(ValueError):
            refund.reject("reason")
