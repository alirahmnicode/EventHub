from datetime import datetime
from typing import Any

from app.schemas.base import ORMModel
from pydantic import BaseModel, Field


class WebhookEventCreate(BaseModel):
    """Internal: built by the webhook handler after signature verification."""

    provider_event_id: str = Field(min_length=1, max_length=255)
    payload: dict[str, Any]


class WebhookEventRead(ORMModel):
    id: int
    provider_event_id: str
    payload: dict[str, Any]
    processed_at: datetime | None


class WebhookAck(BaseModel):
    """Response to the provider. Return 200 for duplicates too."""

    received: bool = True
    duplicate: bool = False
