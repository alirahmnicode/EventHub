from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, uuid_pk
from .enums import ReservationStatus

if TYPE_CHECKING:
    from .order import Order
    from .ticket_type import TicketType


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = uuid_pk()
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ticket_type_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ticket_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        SAEnum(ReservationStatus, name="reservation_status"),
        nullable=False,
        default=ReservationStatus.pending,
        index=True,
    )
    # Client-supplied key so retried reservation requests are safely
    # deduplicated at the DB layer.
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ticket_type: Mapped["TicketType"] = relationship(back_populates="reservations")
    order: Mapped["Order | None"] = relationship(
        back_populates="reservation", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_reservation_idempotency_key"),
        CheckConstraint("quantity > 0", name="ck_reservation_quantity_positive"),
    )
