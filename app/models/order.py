from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import OrderStatus

if TYPE_CHECKING:
    from .reservation import Reservation


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id"),
        nullable=False,
        unique=True,
    )

    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        nullable=False,
        default=OrderStatus.pending,
    )

    provider_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    reservation: Mapped["Reservation"] = relationship(
        back_populates="order",
    )
