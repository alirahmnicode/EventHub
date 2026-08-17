from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .user import User


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        back_populates="venues",
    )

    events: Mapped[list["Event"]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_venue_capacity_positive"),
    )
