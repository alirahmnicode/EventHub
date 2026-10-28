from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import TicketType
from app.schemas import TicketTypeCreate, TicketTypeUpdate


class CRUDTicketType(CRUDBase[TicketType, TicketTypeCreate, TicketTypeUpdate]):
    async def search(
        self,
        db: AsyncSession,
        *,
        event_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[TicketType]:
        filters = []
        if event_id:
            filters.append(TicketType.event_id == event_id)
        return await self.get_multi(
            db,
            filters=filters,
            order_by=(TicketType.event_id, TicketType.id),
            offset=offset,
            limit=limit,
        )

    async def get_for_update(self, db: AsyncSession, id: int) -> TicketType | None:
        """SELECT ... FOR UPDATE: locks the row until commit/rollback so reserved
        and sold counts can't change between our check and our write."""
        stmt = select(TicketType).where(TicketType.id == id).with_for_update()
        return await db.scalar(stmt)


ticket_type = CRUDTicketType(TicketType)
