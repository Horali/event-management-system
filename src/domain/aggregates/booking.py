"""Booking Aggregate Root.

Manages the reservation lifecycle for ticket purchases.
A Booking is created when a Customer reserves tickets for an Event.

UC8  — Create Ticket Booking : __init__
UC9  — Calculate Total Price  : total_price property
UC10 — Pay Booking            : pay()
UC11 — Expire Booking         : expire()
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from src.domain.entities.ticket import Ticket
from src.domain.events.base import BaseDomainEvent
from src.domain.events.booking_expired import BookingExpired
from src.domain.events.booking_paid import BookingPaid
from src.domain.events.ticket_checked_in import TicketCheckedIn
from src.domain.events.ticket_reserved import TicketReserved
from src.domain.value_objects.booking_id import BookingID
from src.domain.value_objects.booking_status import BookingStatus
from src.domain.value_objects.customer_id import CustomerID
from src.domain.value_objects.event_id import EventID
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.ticket_category_id import TicketCategoryID
from src.domain.value_objects.ticket_code import TicketCode
from src.domain.value_objects.ticket_status import TicketStatus

# Payment deadline: 15 minutes after booking creation
PAYMENT_DEADLINE_MINUTES = 15


class Booking:
    """Aggregate Root for the Booking domain.

    Invariants enforced by this class:
    - quantity > 0                          (enforced by Quantity)
    - booking can only be created for a Published event (enforced by caller)
    - booking can only be created for an active TicketCategory (enforced by caller)
    - booking can only be created within the sales period (enforced by caller)
    - quantity must not exceed remaining quota (enforced by caller)
    - a customer cannot have more than one active booking per event (enforced by caller)
    - status transitions follow the defined lifecycle
    """

    # ------------------------------------------------------------------ #
    # Construction — UC8: Create Ticket Booking                           #
    # ------------------------------------------------------------------ #

    def __init__(
        self,
        id: BookingID,
        customer_id: CustomerID,
        event_id: EventID,
        ticket_category_id: TicketCategoryID,
        unit_price: Money,
        quantity: Quantity,
        created_at: datetime | None = None,
    ) -> None:
        now = created_at or datetime.now(tz=timezone.utc)

        self._id: BookingID = id
        self._customer_id: CustomerID = customer_id
        self._event_id: EventID = event_id
        self._ticket_category_id: TicketCategoryID = ticket_category_id
        self._unit_price: Money = unit_price
        self._quantity: Quantity = quantity
        self._status: BookingStatus = BookingStatus.PENDING_PAYMENT
        self._created_at: datetime = now
        self._payment_deadline: datetime = now + timedelta(
            minutes=PAYMENT_DEADLINE_MINUTES
        )
        self._tickets: List[Ticket] = []
        self._pending_domain_events: List[BaseDomainEvent] = []

        self._pending_domain_events.append(
            TicketReserved(
                occurred_at=now,
                booking_id=self._id,
                customer_id=self._customer_id,
                event_id=self._event_id,
                ticket_category_id=self._ticket_category_id,
                quantity=self._quantity.value,
            )
        )

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def id(self) -> BookingID:
        return self._id

    @property
    def customer_id(self) -> CustomerID:
        return self._customer_id

    @property
    def event_id(self) -> EventID:
        return self._event_id

    @property
    def ticket_category_id(self) -> TicketCategoryID:
        return self._ticket_category_id

    @property
    def unit_price(self) -> Money:
        return self._unit_price

    @property
    def quantity(self) -> Quantity:
        return self._quantity

    @property
    def status(self) -> BookingStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def payment_deadline(self) -> datetime:
        return self._payment_deadline

    @property
    def total_price(self) -> Money:
        """UC9: Total price = unit price × quantity."""
        return self._unit_price * self._quantity.value

    @property
    def tickets(self) -> List[Ticket]:
        """Return a shallow copy of issued tickets."""
        return list(self._tickets)

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

    def pay(self, payment_amount: Money, paid_at: datetime | None = None) -> None:
        """UC10: Transition PendingPayment → Paid.

        Guards (validate-first):
        1. Status must be PendingPayment.
        2. Payment must not be after the deadline.
        3. Payment amount must equal the total price.
        """
        now = paid_at or datetime.now(tz=timezone.utc)

        if self._status != BookingStatus.PENDING_PAYMENT:
            raise ValueError(
                f"Cannot pay booking with status {self._status.value}"
            )
        if now > self._payment_deadline:
            raise ValueError(
                "Cannot pay booking: payment deadline has passed"
            )
        if payment_amount != self.total_price:
            raise ValueError(
                f"Payment amount {payment_amount.amount} does not match "
                f"total price {self.total_price.amount}"
            )

        self._status = BookingStatus.PAID
        # Issue one Ticket per quantity unit with unique codes
        for _ in range(self._quantity.value):
            self._tickets.append(Ticket(code=TicketCode.generate()))
        self._pending_domain_events.append(
            BookingPaid(
                occurred_at=now,
                booking_id=self._id,
            )
        )

    def expire(self, expired_at: datetime | None = None) -> None:
        """UC11: Transition PendingPayment → Expired.

        Called by the system when the payment deadline has passed
        and the booking has not been paid.

        Guards (validate-first):
        1. Status must be PendingPayment — a Paid booking cannot expire.
        """
        now = expired_at or datetime.now(tz=timezone.utc)

        if self._status == BookingStatus.PAID:
            raise ValueError("Cannot expire a booking that has already been paid")
        if self._status != BookingStatus.PENDING_PAYMENT:
            raise ValueError(
                f"Cannot expire booking with status {self._status.value}"
            )

        self._status = BookingStatus.EXPIRED
        self._pending_domain_events.append(
            BookingExpired(
                occurred_at=now,
                booking_id=self._id,
            )
        )

    def check_in_ticket(
        self,
        ticket_code: TicketCode,
        checked_in_at: datetime | None = None,
    ) -> None:
        """UC13: Check in a ticket by its code.

        Guards (validate-first):
        1. Ticket with given code must exist in this booking.
        2. Ticket status must be Active — already checked-in tickets are rejected.
        """
        now = checked_in_at or datetime.now(tz=timezone.utc)

        ticket = next(
            (t for t in self._tickets if t.code == ticket_code),
            None,
        )
        if ticket is None:
            raise ValueError(
                f"Ticket with code {ticket_code} not found in this booking"
            )
        if ticket.status == TicketStatus.CHECKED_IN:
            raise ValueError(
                f"Ticket {ticket_code} has already been checked in"
            )
        if ticket.status != TicketStatus.ACTIVE:
            raise ValueError(
                f"Cannot check in ticket with status {ticket.status.value}"
            )

        ticket.status = TicketStatus.CHECKED_IN
        self._pending_domain_events.append(
            TicketCheckedIn(
                occurred_at=now,
                booking_id=self._id,
                ticket_code=ticket_code,
            )
        )

    def __repr__(self) -> str:
        return (
            f"Booking(id={self._id!r}, status={self._status.value!r}, "
            f"quantity={self._quantity.value})"
        )
