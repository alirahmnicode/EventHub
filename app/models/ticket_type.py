from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .reservation import Reservation


class TicketType(Base):
    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    total_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    sold_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    sales_start_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    sales_end_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    event: Mapped["Event"] = relationship(
        back_populates="ticket_types",
    )

    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="ticket_type",
    )
