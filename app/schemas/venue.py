from app.schemas.base import ORMModel
from pydantic import BaseModel, Field


class VenueBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=300)
    city: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0)


class VenueCreate(VenueBase):
    """created_by is set from the authenticated user, not the request."""


class VenueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=300)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, gt=0)


class VenueRead(ORMModel, VenueBase):
    id: int
    created_by: int
