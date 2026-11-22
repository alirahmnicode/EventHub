from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReservationStatus
from app.schemas.base import ORMModel


class ReservationCreate(BaseModel):
    """user_id comes from the auth user. The idempotency key can also be
    read from an `Idempotency-Key` header instead of the body."""

    ticket_type_id: int
    quantity: int = Field(gt=0, le=10)


class ReservationRead(ORMModel):
    id: int
    user_id: int
    ticket_type_id: int
    quantity: int
    status: ReservationStatus
    idempotency_key: str
    expires_at: datetime
    created_at: datetime
