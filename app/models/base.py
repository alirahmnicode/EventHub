import uuid

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db.database import Base


def uuid_pk() -> Mapped[str]:
    """Shared UUID primary key helper (swap for postgresql.UUID if you're
    on Postgres and want a native column type)."""
    return mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
