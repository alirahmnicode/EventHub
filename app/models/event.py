from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, uuid_pk
from .enums import EventStatus

if TYPE_CHECKING:
    from .ticket_type import TicketType
    from .venue import Venue


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = uuid_pk()
    venue_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        SAEnum(EventStatus, name="event_status"),
        nullable=False,
        default=EventStatus.draft,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)

    venue: Mapped["Venue"] = relationship(back_populates="events")
    ticket_types: Mapped[list["TicketType"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_event_end_after_start"),
    )
