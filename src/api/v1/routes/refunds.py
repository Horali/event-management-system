from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List
from pydantic import BaseModel

from src.api.dependencies import (
    get_refund_repository,
    get_request_refund_handler,
    get_approve_refund_handler,
    get_reject_refund_handler,
    get_mark_refund_paid_out_handler,
)
from src.infrastructure.repositories import RefundRepository
from src.api.v1.schemas.refund_schemas import RejectRefundRequest, MarkRefundPaidOutRequest
from src.application.commands.refund_commands import (
    RequestRefundCommand,
    RequestRefundHandler,
    ApproveRefundCommand,
    ApproveRefundHandler,
    RejectRefundCommand,
    RejectRefundHandler,
    MarkRefundPaidOutCommand,
    MarkRefundPaidOutHandler,
)
from src.application.dtos.refund_dtos import RefundDTO
from src.domain.value_objects.refund_id import RefundID

router = APIRouter(prefix="/refunds", tags=["Refunds"])

class RequestRefundRequest(BaseModel):
    booking_id: UUID

@router.post("", status_code=201)
def request_refund(
    request: RequestRefundRequest,
    handler: RequestRefundHandler = Depends(get_request_refund_handler)
):
    command = RequestRefundCommand(booking_id=request.booking_id)
    refund_id = handler.handle(command)
    return {"id": refund_id}

@router.post("/{refund_id}/approve")
def approve_refund(
    refund_id: UUID,
    handler: ApproveRefundHandler = Depends(get_approve_refund_handler)
):
    command = ApproveRefundCommand(refund_id=refund_id)
    handler.handle(command)
    return {"message": "Refund approved successfully"}

@router.post("/{refund_id}/reject")
def reject_refund(
    refund_id: UUID,
    request: RejectRefundRequest,
    handler: RejectRefundHandler = Depends(get_reject_refund_handler)
):
    command = RejectRefundCommand(refund_id=refund_id, reason=request.reason)
    handler.handle(command)
    return {"message": "Refund rejected successfully"}

@router.post("/{refund_id}/payout")
def payout_refund(
    refund_id: UUID,
    request: MarkRefundPaidOutRequest,
    handler: MarkRefundPaidOutHandler = Depends(get_mark_refund_paid_out_handler)
):
    command = MarkRefundPaidOutCommand(
        refund_id=refund_id,
        payment_reference=request.payment_reference,
    )
    handler.handle(command)
    return {"message": "Refund marked as paid out successfully"}

@router.get("/{refund_id}", response_model=RefundDTO)
def get_refund(
    refund_id: UUID,
    refund_repo: RefundRepository = Depends(get_refund_repository)
):
    refund = refund_repo.find_by_id(RefundID(refund_id))
    if not refund:
        raise HTTPException(status_code=404, detail=f"Refund with ID {refund_id} was not found.")
    return RefundDTO.from_domain(refund)

@router.get("", response_model=List[RefundDTO])
def list_refunds(
    refund_repo: RefundRepository = Depends(get_refund_repository)
):
    refunds = refund_repo.find_all()
    return [RefundDTO.from_domain(r) for r in refunds]