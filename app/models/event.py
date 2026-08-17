from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import EventStatus

if TYPE_CHECKING:
    from .ticket_type import TicketType
    from .venue import Venue


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    status: Mapped[EventStatus] = mapped_column(
        nullable=False,
        default=EventStatus.draft,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    # Relationships
    venue: Mapped["Venue"] = relationship(
        back_populates="events",
    )

    creator: Mapped["User"] = relationship(
        back_populates="events",
    )

    ticket_types: Mapped[list["TicketType"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
