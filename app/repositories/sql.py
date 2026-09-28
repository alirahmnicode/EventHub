from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.event_record import EventRecord
from app.repositories.interfaces import NotFoundError


def _to_record(event: Event) -> EventRecord:
    """The only place scalar columns are read off a live ORM instance."""
    return EventRecord(
        id=event.id,
        venue_id=event.venue_id,
        title=event.title,
        description=event.description,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        status=event.status,
        created_by=event.created_by,
    )


def _apply_record(record: EventRecord, event: Event) -> None:
    """The only place scalar columns are written onto a live ORM
    instance. Deliberately never touches venue/creator/ticket_types."""
    event.venue_id = record.venue_id
    event.title = record.title
    event.description = record.description
    event.starts_at = record.starts_at
    event.ends_at = record.ends_at
    event.status = record.status
    event.created_by = record.created_by


class SqlEventRepository:
    """Implements the Repository[EventRecord] Protocol structurally —
    no inheritance needed."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: int) -> EventRecord:
        result = await self._session.execute(select(Event).where(Event.id == id))
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event", id)
        return _to_record(event)

    async def get_all(self, page: int, page_size: int) -> tuple[list[EventRecord], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(Event)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(Event)
            .order_by(Event.starts_at)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        events = result.scalars().all()
        return [_to_record(e) for e in events], total

    async def add(self, record: EventRecord) -> EventRecord:
        event = Event()
        _apply_record(record, event)
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)  # populate the DB-assigned id
        return _to_record(event)

    async def update(self, id: int, record: EventRecord) -> EventRecord:
        result = await self._session.execute(select(Event).where(Event.id == id))
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event", id)

        _apply_record(record, event)
        await self._session.commit()
        return _to_record(event)

    async def delete(self, id: int) -> None:
        result = await self._session.execute(select(Event).where(Event.id == id))
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event", id)

        await self._session.delete(event)
        await self._session.commit()
