from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ReservationStatus, enum_column

if TYPE_CHECKING:
    from app.models.ticket_type import TicketType
    from app.models.user import User


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        # Same user + same key = same request (safe client retries).
        UniqueConstraint("user_id", "idempotency_key"),
        # For the "expire stale pending reservations" job.
        Index("ix_reservations_status_expires_at", "status", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    ticket_type_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_types.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int]
    status: Mapped[ReservationStatus] = mapped_column(
        enum_column(ReservationStatus, "reservation_status"),
        default=ReservationStatus.PENDING,
        server_default=ReservationStatus.PENDING.value,
    )
    idempotency_key: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship()
    ticket_type: Mapped["TicketType"] = relationship()
