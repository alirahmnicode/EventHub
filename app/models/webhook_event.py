from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider_event_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
