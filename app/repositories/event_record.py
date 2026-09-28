from dataclasses import dataclass
from datetime import datetime

from app.models.enums import EventStatus


@dataclass
class EventRecord:
    id: int | None
    venue_id: int
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    status: EventStatus
    created_by: int
