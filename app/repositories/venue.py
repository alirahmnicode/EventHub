from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Venue
from app.schemas.venue import VenueCreate, VenueRead, VenueUpdate


class VenueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Venue | None:
        return await self.session.get(Venue, id)

    async def get_list(
        self,
        *,
        filters: Sequence[ColumnElement[bool]] = (),
        order_by: Sequence[Any] = (),
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Venue]:
        stmt = select(Venue).where(*filters)
        stmt = stmt.order_by(*(order_by or sa_inspect(Venue).primary_key))
        result = await self.session.scalars(stmt.offset(offset).limit(limit))
        return result.all()

    async def create(self, obj_in: VenueCreate, **extra: Any) -> Venue:
        """`extra` carries server-controlled fields such as created_by."""
        obj = Venue(**obj_in.model_dump(), **extra)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, db_obj: Venue, obj_in: VenueUpdate) -> Venue:
        columns = sa_inspect(Venue).columns
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            if value is None and not columns[field].nullable:
                continue
            setattr(db_obj, field, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Venue) -> None:
        await self.session.delete(db_obj)
        await self.session.commit()
