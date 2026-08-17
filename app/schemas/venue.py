from pydantic import BaseModel, ConfigDict, Field


class VenueBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        examples=["Baku Convention Center"],
    )

    address: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["130 Tabriz Street"],
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Baku"],
    )

    capacity: int = Field(
        ...,
        gt=0,
        examples=[3500],
    )


class VenueCreateSchema(VenueBase):
    pass


class VenueUpdateSchema(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        examples=["Updated Venue Name"],
    )

    address: str | None = Field(
        default=None,
        min_length=5,
        max_length=500,
        examples=["Updated Address"],
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        examples=["Baku"],
    )

    capacity: int | None = Field(
        default=None,
        gt=0,
        examples=[5000],
    )


class VenueReadSchema(VenueBase):
    id: int
    created_by: int

    model_config = ConfigDict(
        from_attributes=True,
    )
