"""SQLAlchemy ORM models for the Event aggregate and TicketCategory entity."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.models.base import Base


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    schedule_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    schedule_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    ticket_categories: Mapped[list[TicketCategoryModel]] = relationship(
        "TicketCategoryModel",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<EventModel id={self.id} name={self.name!r} status={self.status!r}>"


class TicketCategoryModel(Base):
    __tablename__ = "ticket_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(10), nullable=False, default="IDR")
    quota: Mapped[int] = mapped_column(Integer, nullable=False)
    sales_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sales_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    event: Mapped[EventModel] = relationship("EventModel", back_populates="ticket_categories")

    def __repr__(self) -> str:
        return f"<TicketCategoryModel id={self.id} name={self.name!r}>"
