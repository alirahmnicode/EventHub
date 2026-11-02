from collections.abc import Sequence

from app.core.exceptions import (
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models.enums import EventStatus, UserRole
from app.models.event import Event
from app.models.user import User
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate, EventUpdate

MAX_PAGE_SIZE = 100


class EventService:
    def __init__(self, repo: EventRepository):
        self.repo = repo

    @staticmethod
    def _can_modify(user: User) -> bool:
        # only admin users can create, update, delete event
        return user.role == UserRole.ADMIN

    async def _get_or_404(self, event_id: int) -> Event:
        event = await self.repo.get(event_id)
        if event is None:
            raise NotFoundError()
        return event

    async def _get_modifiable(self, event_id: int, user: User) -> Event:
        event = await self._get_or_404(event_id)
        if not self._can_modify(user):
            raise PermissionDeniedError()
        return event

    def _is_valid_date_range(self, starts_at, ends_at) -> bool:
        if starts_at is None or ends_at is None:
            return False
        return starts_at < ends_at

    async def get_event(self, event_id: int, user: User | None = None) -> Event:
        # only admin user can access draft events
        event = await self._get_or_404(event_id)

        if event.status in (EventStatus.PUBLISHED, EventStatus.CANCELLED):
            return event

        # draft (or any non-public status): admin only
        if user is None or user.role != UserRole.ADMIN:
            raise PermissionDeniedError(
                message="Current user does not have access to this object."
            )
        return event

    async def list_events(
        self,
        *,
        user: User | None = None,
        search: str | None = None,
        venue_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Event]:
        filters = []

        if user is None or user.role != UserRole.ADMIN:
            filters.append(Event.status != EventStatus.DRAFT)
        if venue_id:
            filters.append(Event.venue_id == venue_id)
        if search:
            filters.append(Event.title.ilike(f"%{search}%"))

        return await self.repo.get_list(
            filters=filters,
            order_by=[Event.id.desc()],
            offset=max(offset, 0),
            limit=min(max(limit, 1), MAX_PAGE_SIZE),
        )

    async def create_event(self, data: EventCreate, user: User) -> Event:
        if not self._can_modify(user):
            raise PermissionDeniedError()

        if not self._is_valid_date_range(data.starts_at, data.ends_at):
            raise DomainValidationError(
                message="The start date must be before the end date."
            )
        return await self.repo.create(data, created_by=user.id)

    async def update_event(self, event_id: int, data: EventUpdate, user: User) -> Event:
        event = await self._get_modifiable(event_id, user)

        # if the dates (start or end) are changing, check date range, otherwise dont check date on partial update
        if data.starts_at is not None or data.ends_at is not None:
            starts_at = (
                data.starts_at if data.starts_at is not None else event.starts_at
            )
            ends_at = data.ends_at if data.ends_at is not None else event.ends_at
            if not self._is_valid_date_range(starts_at, ends_at):
                raise DomainValidationError(
                    message="The start date must be before the end date."
                )
        return await self.repo.update(event, data)

    async def delete_event(self, event_id: int, user: User) -> None:
        event = await self._get_modifiable(event_id, user)
        await self.repo.delete(event)
