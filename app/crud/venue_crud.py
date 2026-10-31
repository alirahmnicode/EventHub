from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models import Venue
from app.schemas import VenueCreate, VenueUpdate


class CRUDVenue(CRUDBase[Venue, VenueCreate, VenueUpdate]):
    async def search(
        self,
        db: AsyncSession,
        *,
        city: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Venue]:
        filters = []
        if city:
            filters.append(func.lower(Venue.city) == city.lower())
        return await self.get_multi(
            db, filters=filters, order_by=(Venue.name,), offset=offset, limit=limit
        )


venue = CRUDVenue(Venue)
