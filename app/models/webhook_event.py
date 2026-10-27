from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    # UNIQUE = idempotency guarantee. Insert first; a duplicate raises
    # IntegrityError (or use INSERT ... ON CONFLICT DO NOTHING).
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql")
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
