from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.aggregates.refund import Refund
from src.domain.value_objects.refund_id import RefundID
from src.domain.value_objects.booking_id import BookingID


class IRefundRepository(ABC):

    @abstractmethod
    def save(self, refund: Refund) -> None:
        """Persist or update a Refund aggregate (upsert semantics)."""

    @abstractmethod
    def find_by_id(self, refund_id: RefundID) -> Optional[Refund]:
        """Return the Refund with the given ID, or None if not found."""

    @abstractmethod
    def find_by_booking_id(self, booking_id: BookingID) -> Optional[Refund]:
        """Return the Refund for a given booking, or None if not found."""

    @abstractmethod
    def find_all(self) -> List[Refund]:
        """Return all Refund aggregates."""
