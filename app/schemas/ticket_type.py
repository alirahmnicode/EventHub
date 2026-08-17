from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketTypeCreateSchema(BaseModel):
    event_id: int
    name: str = Field(min_length=1, max_length=100)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_quantity: int = Field(gt=0)
    reserved_quantity: int = Field(default=0, ge=0)
    sold_quantity: int = Field(default=0, ge=0)
    sales_start_at: datetime | None = None
    sales_end_at: datetime | None = None


class TicketTypeUpdateSchema(BaseModel):
    event_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    total_quantity: int | None = Field(default=None, gt=0)
    reserved_quantity: int | None = Field(default=None, ge=0)
    sold_quantity: int | None = Field(default=None, ge=0)
    sales_start_at: datetime | None = None
    sales_end_at: datetime | None = None


class TicketTypeReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    name: str
    price_cents: int
    currency: str
    total_quantity: int
    reserved_quantity: int
    sold_quantity: int
    sales_start_at: datetime | None
    sales_end_at: datetime | None
