from collections.abc import Sequence

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.enums import UserRole
from app.models.user import User
from app.models.venue import Venue
from app.repositories.venue import VenueRepository
from app.schemas.venue import VenueCreate, VenueUpdate

MAX_PAGE_SIZE = 100


class VenueService:
    def __init__(self, repo: VenueRepository):
        self.repo = repo

    @staticmethod
    def _can_modify(user: User) -> bool:
        # only admin users can create, update, delete venues
        return user.role == UserRole.ADMIN

    async def _get_or_404(self, venue_id: int) -> Venue:
        venue = await self.repo.get(venue_id)
        if venue is None:
            raise NotFoundError()
        return venue

    async def _get_modifiable(self, venue_id: int, user: User) -> Venue:
        venue = await self._get_or_404(venue_id)
        if not self._can_modify(user):
            raise PermissionDeniedError()
        return venue

    async def get_venue(self, venue_id: int) -> Venue:
        return await self._get_or_404(venue_id)

    async def list_venues(
        self,
        *,
        search: str | None = None,
        city: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Venue]:
        filters = []
        if search:
            filters.append(Venue.name.ilike(f"%{search}%"))
        if city:
            filters.append(Venue.city == city)

        return await self.repo.get_list(
            filters=filters,
            order_by=[Venue.id.desc()],
            offset=max(skip, 0),
            limit=min(max(limit, 1), MAX_PAGE_SIZE),
        )

    async def create_venue(self, data: VenueCreate, user: User) -> Venue:
        if not self._can_modify(user):
            raise PermissionDeniedError()
        return await self.repo.create(data, created_by=user.id)

    async def update_venue(self, venue_id: int, data: VenueUpdate, user: User) -> Venue:
        venue = await self._get_modifiable(venue_id, user)
        return await self.repo.update(venue, data)

    async def delete_venue(self, venue_id: int, user: User) -> None:
        venue = await self._get_modifiable(venue_id, user)
        await self.repo.delete(venue)
