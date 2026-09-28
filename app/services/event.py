from dataclasses import replace

from app.models.event import EventStatus
from app.repositories.event_record import EventRecord
from app.repositories.interfaces import Repository, VenueLookup
from app.schemas.event import EventCreateSchema, EventUpdateSchema


class InvalidEventTimesError(Exception):
    def __init__(self):
        super().__init__("starts_at must be before ends_at")


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: EventStatus, target: EventStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition event from {current} to {target}")


class CannotDeletePublishedEventError(Exception):
    def __init__(self, event_id: int):
        self.event_id = event_id
        super().__init__(f"Cannot delete published event {event_id}; cancel it first")


# valid_transitions[current_status] = set of statuses it can move to
_VALID_TRANSITIONS: dict[EventStatus, set[EventStatus]] = {
    EventStatus.draft: {EventStatus.published, EventStatus.cancelled},
    EventStatus.published: {EventStatus.cancelled},
    EventStatus.cancelled: set(),
}


class EventService:
    def __init__(
        self, event_repository: Repository[EventRecord], venue_lookup: VenueLookup
    ):
        self._repo = event_repository
        self._venues = venue_lookup

    async def create_event(
        self, data: EventCreateSchema, created_by: int
    ) -> EventRecord:
        await self._venues.get(data.venue_id)

        if data.starts_at >= data.ends_at:
            raise InvalidEventTimesError()

        record = EventRecord(
            id=None,
            venue_id=data.venue_id,
            title=data.title,
            description=data.description,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            status=EventStatus.draft,
            created_by=created_by,
        )
        return await self._repo.add(record)

    async def get_event(self, event_id: int) -> EventRecord:
        return await self._repo.get(event_id)

    async def list_events(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[EventRecord], int]:
        return await self._repo.get_all(page, page_size)

    async def update_event(self, event_id: int, data: EventUpdateSchema) -> EventRecord:
        existing = await self._repo.get(event_id)

        # only overwrite fields the caller actually provided
        changes = data.model_dump(exclude_unset=True)
        updated = replace(existing, **changes)

        if updated.starts_at >= updated.ends_at:
            raise InvalidEventTimesError()

        return await self._repo.update(event_id, updated)

    async def change_status(
        self, event_id: int, new_status: EventStatus
    ) -> EventRecord:
        # check that the transition is valid before updating the record
        existing = await self._repo.get(event_id)

        if new_status not in _VALID_TRANSITIONS[existing.status]:
            raise InvalidStatusTransitionError(existing.status, new_status)

        updated = replace(existing, status=new_status)
        return await self._repo.update(event_id, updated)

    async def delete_event(self, event_id: int) -> None:
        existing = await self._repo.get(event_id)

        if existing.status == EventStatus.published:
            raise CannotDeletePublishedEventError(event_id)

        await self._repo.delete(event_id)
