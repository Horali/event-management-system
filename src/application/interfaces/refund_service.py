from abc import ABC, abstractmethod
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.money import Money


class IRefundPaymentService(ABC):
    """Interface for external refund payout / bank service integration."""

    @abstractmethod
    def process_refund_payout(self, refund_id: RefundID, amount: Money) -> str:
        """Process a refund payout.

        Returns:
            str: A transaction payment reference string from the payment service.
        """
        pass
