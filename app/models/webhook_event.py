from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, uuid_pk


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[str] = uuid_pk()
    # Unique ID assigned by the upstream provider (e.g. Stripe event id).
    # The unique constraint is what gives you idempotent webhook processing.
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("provider_event_id", name="uq_webhookevent_provider_event_id"),
    )
