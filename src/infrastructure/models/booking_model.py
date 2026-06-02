"""SQLAlchemy ORM models for the Booking aggregate and Ticket entity."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.models.base import Base


class BookingModel(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ticket_category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    unit_price_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    unit_price_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="IDR")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PendingPayment")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tickets: Mapped[list[TicketModel]] = relationship(
        "TicketModel",
        back_populates="booking",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BookingModel id={self.id} status={self.status!r}>"


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Active")

    booking: Mapped[BookingModel] = relationship("BookingModel", back_populates="tickets")

    def __repr__(self) -> str:
        return f"<TicketModel code={self.code!r} status={self.status!r}>"
