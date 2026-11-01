from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Event
from app.schemas.event import EventCreate, EventUpdate


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Event | None:
        stmt = (
            select(Event)
            .where(Event.id == id)
            .options(
                joinedload(Event.venue),
                selectinload(Event.ticket_types),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        *,
        filters: Sequence[ColumnElement[bool]] = (),
        order_by: Sequence[Any] = (),
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Event]:
        stmt = select(Event).where(*filters)
        stmt = stmt.order_by(*(order_by or sa_inspect(Event).primary_key))
        result = await self.session.scalars(stmt.offset(offset).limit(limit))
        return result.all()

    async def create(self, obj_in: EventCreate, **extra: Any) -> Event:
        """`extra` carries server-controlled fields such as created_by."""
        obj = Event(**obj_in.model_dump(), **extra)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, db_obj: Event, obj_in: EventUpdate) -> Event:
        columns = sa_inspect(Event).columns
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            if value is None and not columns[field].nullable:
                continue
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Event) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
