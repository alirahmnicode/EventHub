from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ReservationStatus

if TYPE_CHECKING:
    from .order import Order
    from .ticket_type import TicketType


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    ticket_type_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_types.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        nullable=False,
        default=ReservationStatus.pending,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="reservations",
    )

    ticket_type: Mapped["TicketType"] = relationship(
        back_populates="reservations",
    )

    order: Mapped["Order | None"] = relationship(
        back_populates="reservation",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_reservation_user_idempotency",
        ),
    )
