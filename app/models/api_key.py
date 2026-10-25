from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_name: Mapped[str] = mapped_column(String(200))
    # Store only a hash (e.g. SHA-256 of the key); never the raw key.
    key_hash: Mapped[str] = mapped_column(String(128), unique=True)
    scopes: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), default=list
    )
    rate_limit_tier: Mapped[str] = mapped_column(
        String(50), default="standard", server_default="standard"
    )
