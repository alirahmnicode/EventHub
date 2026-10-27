from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.event import Event


class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = (CheckConstraint("capacity > 0", name="capacity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(300))
    city: Mapped[str] = mapped_column(String(100), index=True)
    capacity: Mapped[int]
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    events: Mapped[list["Event"]] = relationship(back_populates="venue")
