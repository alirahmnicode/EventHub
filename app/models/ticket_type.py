from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, uuid_pk

if TYPE_CHECKING:
    from .event import Event
    from .reservation import Reservation


class TicketType(Base):
    __tablename__ = "ticket_types"

    id: Mapped[str] = uuid_pk()
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sold_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sales_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sales_end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    event: Mapped["Event"] = relationship(back_populates="ticket_types")
    reservations: Mapped[list["Reservation"]] = relationship(
        back_populates="ticket_type", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="ck_tickettype_price_nonneg"),
        CheckConstraint("total_quantity >= 0", name="ck_tickettype_total_nonneg"),
        CheckConstraint("reserved_quantity >= 0", name="ck_tickettype_reserved_nonneg"),
        CheckConstraint("sold_quantity >= 0", name="ck_tickettype_sold_nonneg"),
        CheckConstraint(
            "reserved_quantity + sold_quantity <= total_quantity",
            name="ck_tickettype_inventory_within_total",
        ),
        CheckConstraint(
            "sales_end_at > sales_start_at", name="ck_tickettype_sales_window"
        ),
    )
