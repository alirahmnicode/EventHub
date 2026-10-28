from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models import Event
from app.models.enums import EventStatus
from app.schemas import EventCreate, EventUpdate


class CRUDEvent(CRUDBase[Event, EventCreate, EventUpdate]):
    async def search(
        self,
        db: AsyncSession,
        *,
        status: EventStatus | None = None,
        venue_id: int | None = None,
        upcoming_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Event]:
        filters = []
        if status:
            filters.append(Event.status == status)
        if venue_id:
            filters.append(Event.venue_id == venue_id)
        if upcoming_only:
            filters.append(Event.starts_at >= datetime.now(timezone.utc))
        return await self.get_multi(
            db,
            filters=filters,
            order_by=(Event.starts_at, Event.id),
            offset=offset,
            limit=limit,
        )

    async def get_with_details(self, db: AsyncSession, id: int) -> Event | None:
        """Event plus venue and ticket types, loaded eagerly (required in async)."""
        stmt = (
            select(Event)
            .where(Event.id == id)
            .options(selectinload(Event.venue), selectinload(Event.ticket_types))
        )
        return await db.scalar(stmt)


event = CRUDEvent(Event)
