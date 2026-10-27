from app.schemas.base import ORMModel
from pydantic import AwareDatetime, BaseModel, Field, computed_field, model_validator


def _check_sales_window(start: AwareDatetime | None, end: AwareDatetime | None) -> None:
    if start is not None and end is not None and end <= start:
        raise ValueError("sales_end_at must be after sales_start_at")


class TicketTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    total_quantity: int = Field(ge=0)
    sales_start_at: AwareDatetime | None = None
    sales_end_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_window(self):
        _check_sales_window(self.sales_start_at, self.sales_end_at)
        return self


class TicketTypeCreate(TicketTypeBase):
    event_id: int


class TicketTypeUpdate(BaseModel):
    """reserved/sold counts are never client-editable."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    total_quantity: int | None = Field(default=None, ge=0)
    sales_start_at: AwareDatetime | None = None
    sales_end_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_window(self):
        _check_sales_window(self.sales_start_at, self.sales_end_at)
        return self


class TicketTypeRead(ORMModel, TicketTypeBase):
    id: int
    event_id: int
    reserved_quantity: int
    sold_quantity: int

    @computed_field
    @property
    def available_quantity(self) -> int:
        return self.total_quantity - self.reserved_quantity - self.sold_quantity
