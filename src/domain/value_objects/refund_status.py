"""RefundStatus Value Object.

Enum representing the lifecycle state of a Refund.
Valid values: Requested, Approved, Rejected, PaidOut.
"""

from enum import Enum


class RefundStatus(str, Enum):
    REQUESTED = "Requested"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PAID_OUT = "PaidOut"
