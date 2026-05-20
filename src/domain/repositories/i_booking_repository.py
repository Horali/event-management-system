"""IBookingRepository — Repository Interface for the Booking aggregate.

Defined in the domain layer as an abstract base class.
The infrastructure layer provides the concrete implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.aggregates.booking import Booking
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID


class IBookingRepository(ABC):

    @abstractmethod
    def save(self, booking: Booking) -> None:
        """Persist or update a Booking aggregate (upsert semantics)."""

    @abstractmethod
    def find_by_id(self, booking_id: BookingID) -> Optional[Booking]:
        """Return the Booking with the given ID, or None if not found."""

    @abstractmethod
    def find_by_customer_and_event(
        self,
        customer_id: CustomerID,
        event_id: EventID,
    ) -> Optional[Booking]:
        """Return an active booking for a customer+event pair, or None.

        Used to enforce the rule: a customer cannot have more than one
        active booking for the same event.
        """

    @abstractmethod
    def find_all(self) -> List[Booking]:
        """Return all Booking aggregates."""
