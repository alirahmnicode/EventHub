import enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=enum.Enum)


class UserRole(enum.StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class EventStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class ReservationStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


def enum_column(enum_cls: type[E], name: str) -> SAEnum:
    """VARCHAR + CHECK constraint (not a native PG enum).

    Native enums are painful to change with Alembic; this stores the
    lowercase value ("customer") and is easy to migrate.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda e: [m.value for m in e],
    )
