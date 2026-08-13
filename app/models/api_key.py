from __future__ import annotations

from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, uuid_pk


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = uuid_pk()
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Never store raw keys — only a hash (e.g. sha256 / bcrypt) of the key.
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g. ["events:read", "reservations:write"]
    scopes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    rate_limit_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard"
    )

    __table_args__ = (UniqueConstraint("key_hash", name="uq_apikey_key_hash"),)
