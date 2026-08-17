from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import EventStatus


class EventBaseSchema(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Baku Tech Conference 2026"],
    )
    description: str | None = Field(
        default=None,
        examples=["A technology conference featuring Python and AI speakers."],
    )
    starts_at: datetime = Field(
        ...,
        examples=["2026-09-15T10:00:00"],
    )
    ends_at: datetime = Field(
        ...,
        examples=["2026-09-15T18:00:00"],
    )
    status: EventStatus = Field(
        default=EventStatus.draft,
        examples=[EventStatus.draft],
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class EventCreateSchema(EventBaseSchema):
    venue_id: int = Field(
        ...,
        gt=0,
        examples=[1],
    )


class EventUpdateSchema(BaseModel):
    venue_id: int | None = Field(
        default=None,
        gt=0,
        examples=[1],
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        examples=["Updated Baku Tech Conference"],
    )
    description: str | None = Field(
        default=None,
        examples=["Updated event description."],
    )
    starts_at: datetime | None = Field(
        default=None,
        examples=["2026-09-15T11:00:00"],
    )
    ends_at: datetime | None = Field(
        default=None,
        examples=["2026-09-15T19:00:00"],
    )
    status: EventStatus | None = Field(
        default=None,
        examples=[EventStatus.published],
    )


class EventReadSchema(EventBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    venue_id: int
    created_by: int
