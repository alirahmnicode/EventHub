from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, uuid_pk
from .enums import OrderStatus

if TYPE_CHECKING:
    from .reservation import Reservation


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = uuid_pk()
    reservation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("reservations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.pending,
        index=True,
    )
    # Reference/ID from the payment provider (e.g. Stripe PaymentIntent id).
    provider_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reservation: Mapped["Reservation"] = relationship(back_populates="order")

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_order_amount_nonneg"),
    )
