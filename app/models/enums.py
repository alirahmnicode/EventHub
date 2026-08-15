import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"


class EventStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    expired = "expired"
    cancelled = "cancelled"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"
