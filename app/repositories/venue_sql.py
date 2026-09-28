from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.venue import Venue
from app.repositories.interfaces import NotFoundError
from app.repositories.venue_record import VenueRecord


class SqlVenueRepository:
    """Satisfies VenueLookup structurally (and could grow full CRUD for
    venue-management routes without EventService needing to know)."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, id: int) -> VenueRecord:
        result = await self._session.execute(select(Venue).where(Venue.id == id))
        venue = result.scalar_one_or_none()
        if venue is None:
            raise NotFoundError("Venue", id)
        return VenueRecord(id=venue.id, name=venue.name)
