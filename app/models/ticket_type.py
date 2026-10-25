from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event


class TicketType(Base):
    __tablename__ = "ticket_types"
    __table_args__ = (
        CheckConstraint("price_cents >= 0", name="price_non_negative"),
        CheckConstraint("total_quantity >= 0", name="total_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="reserved_non_negative"),
        CheckConstraint("sold_quantity >= 0", name="sold_non_negative"),
        # Inventory can never be oversold, even under concurrent writes.
        CheckConstraint(
            "reserved_quantity + sold_quantity <= total_quantity",
            name="no_oversell",
        ),
        CheckConstraint(
            "sales_end_at IS NULL OR sales_start_at IS NULL OR sales_end_at > sales_start_at",
            name="sales_window_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    price_cents: Mapped[int]
    currency: Mapped[str] = mapped_column(
        String(3), default="USD", server_default="USD"
    )
    total_quantity: Mapped[int]
    reserved_quantity: Mapped[int] = mapped_column(default=0, server_default="0")
    sold_quantity: Mapped[int] = mapped_column(default=0, server_default="0")
    sales_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sales_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    event: Mapped["Event"] = relationship(back_populates="ticket_types")
