from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)

    partner_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    key_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    scopes: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    rate_limit_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="standard",
    )
