from app.schemas.base import ORMModel
from app.schemas.ticket_type import TicketTypeRead
from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.models.enums import EventStatus
from app.schemas.venue import VenueRead


def _check_dates(starts: AwareDatetime | None, ends: AwareDatetime | None) -> None:
    if starts is not None and ends is not None and ends <= starts:
        raise ValueError("ends_at must be after starts_at")


class EventBase(BaseModel):
    venue_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def validate_dates(self):
        _check_dates(self.starts_at, self.ends_at)
        return self


class EventCreate(EventBase):
    """New events start as draft; created_by comes from the auth user."""


class EventUpdate(BaseModel):
    venue_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None
    status: EventStatus | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        _check_dates(self.starts_at, self.ends_at)
        return self


class EventRead(ORMModel, EventBase):
    id: int
    status: EventStatus
    created_by: int


class EventDetail(EventRead):
    """Needs selectinload(Event.venue, Event.ticket_types) in the query."""

    venue: VenueRead
    ticket_types: list[TicketTypeRead] = []
