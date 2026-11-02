from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket_type import TicketType
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate


class TicketTypeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> TicketType | None:
        return await self.session.get(TicketType, id)

    async def get_for_update(self, id: int) -> TicketType | None:
        """Row-locked read. Use it for stock changes (reserve/sell) to avoid races."""
        stmt = select(TicketType).where(TicketType.id == id).with_for_update()
        return await self.session.scalar(stmt)

    async def get_list(
        self,
        *,
        filters: Sequence[ColumnElement[bool]] = (),
        order_by: Sequence[Any] = (),
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[TicketType]:
        stmt = select(TicketType).where(*filters)
        stmt = stmt.order_by(*(order_by or sa_inspect(TicketType).primary_key))
        result = await self.session.scalars(stmt.offset(offset).limit(limit))
        return result.all()

    async def create(self, obj_in: TicketTypeCreate, **extra: Any) -> TicketType:
        obj = TicketType(**obj_in.model_dump(), **extra)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, db_obj: TicketType, obj_in: TicketTypeUpdate) -> TicketType:
        columns = sa_inspect(TicketType).columns
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            # Sending null for a required column means "leave unchanged".
            if value is None and not columns[field].nullable:
                continue
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: TicketType) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
