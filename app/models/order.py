from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OrderStatus, enum_column

if TYPE_CHECKING:
    from app.models.reservation import Reservation


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("amount_cents >= 0", name="amount_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"), index=True
    )
    amount_cents: Mapped[int]
    status: Mapped[OrderStatus] = mapped_column(
        enum_column(OrderStatus, "order_status"),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        index=True,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reservation: Mapped["Reservation"] = relationship()
