from __future__ import annotations

from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, uuid_pk


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id: Mapped[str] = uuid_pk()
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    # e.g. {"rollout_percentage": 25, "allowed_user_ids": [...], "env": "prod"}
    rollout_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (UniqueConstraint("key", name="uq_featureflag_key"),)
