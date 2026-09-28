from app.repositories.event_record import EventRecord
from app.repositories.interfaces import NotFoundError
from app.repositories.venue_record import VenueRecord


class FakeEventRepository:
    """Satisfies Repository[EventRecord] structurally. No sqlalchemy
    import anywhere in this file."""

    def __init__(self, items: list[EventRecord] | None = None):
        self._items = {i.id: i for i in (items or [])}
        self._next_id = max([i.id for i in self._items.values() if i.id], default=0) + 1

    async def get(self, id: int) -> EventRecord:
        try:
            return self._items[id]
        except KeyError:
            raise NotFoundError("Event", id)

    async def get_all(self, page: int, page_size: int) -> tuple[list[EventRecord], int]:
        all_items = list(self._items.values())
        start = (page - 1) * page_size
        return all_items[start:start + page_size], len(all_items)

    async def add(self, record: EventRecord) -> EventRecord:
        saved = record if record.id is not None else _with_id(record, self._next_id)
        self._items[saved.id] = saved
        self._next_id += 1
        return saved

    async def update(self, id: int, record: EventRecord) -> EventRecord:
        if id not in self._items:
            raise NotFoundError("Event", id)
        self._items[id] = record
        return record

    async def delete(self, id: int) -> None:
        if id not in self._items:
            raise NotFoundError("Event", id)
        del self._items[id]


def _with_id(record: EventRecord, new_id: int) -> EventRecord:
    from dataclasses import replace
    return replace(record, id=new_id)


class FakeVenueLookup:
    """Satisfies VenueLookup structurally. No sqlalchemy import."""

    def __init__(self, venues: list[VenueRecord] | None = None):
        self._venues = {v.id: v for v in (venues or [])}

    async def get(self, id: int) -> VenueRecord:
        try:
            return self._venues[id]
        except KeyError:
            raise NotFoundError("Venue", id)
