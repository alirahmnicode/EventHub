from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventStatus, enum_column

if TYPE_CHECKING:
    from app.models.ticket_type import TicketType
    from app.models.venue import Venue


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="ends_after_starts"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[EventStatus] = mapped_column(
        enum_column(EventStatus, "event_status"),
        default=EventStatus.DRAFT,
        server_default=EventStatus.DRAFT.value,
        index=True,
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))

    venue: Mapped["Venue"] = relationship(back_populates="events")
    ticket_types: Mapped[list["TicketType"]] = relationship(back_populates="event")
