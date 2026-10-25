from datetime import datetime

from app.schemas.base import ORMModel
from pydantic import BaseModel, Field

from app.models.enums import ReservationStatus


class ReservationCreate(BaseModel):
    """user_id comes from the auth user. The idempotency key can also be
    read from an `Idempotency-Key` header instead of the body."""

    ticket_type_id: int
    quantity: int = Field(gt=0, le=10)
    idempotency_key: str = Field(min_length=1, max_length=255)


class ReservationRead(ORMModel):
    id: int
    user_id: int
    ticket_type_id: int
    quantity: int
    status: ReservationStatus
    idempotency_key: str
    expires_at: datetime
    created_at: datetime
