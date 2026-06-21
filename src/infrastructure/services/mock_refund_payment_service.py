import uuid
from src.application.interfaces.refund_service import IRefundPaymentService
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.money import Money

class MockRefundPaymentService(IRefundPaymentService):
    """Mock implementation of IRefundPaymentService that generates a dummy transaction reference."""

    def process_refund_payout(self, refund_id: RefundID, amount: Money) -> str:
        ref = f"REF-TXN-{uuid.uuid4().hex[:8].upper()}"
        print(f"[Refund Service] Processing payout of {amount.amount} {amount.currency} for refund {refund_id.value}. Ref: {ref}")
        return ref