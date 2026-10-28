from datetime import datetime

from pydantic import BaseModel

from app.models.enums import OrderStatus
from app.schemas.base import ORMModel


class OrderCreate(BaseModel):
    """amount_cents is computed server-side from the reservation; never trust a client price."""

    reservation_id: int


class OrderRead(ORMModel):
    id: int
    reservation_id: int
    amount_cents: int
    status: OrderStatus
    provider_reference: str | None
    created_at: datetime
