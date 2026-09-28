from typing import Protocol

from app.repositories.venue_record import VenueRecord


class NotFoundError(Exception):
    def __init__(self, resource: str, resource_id: int):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} not found: {resource_id}")


class Repository[T](Protocol):
    async def get(self, id: int) -> T: ...

    async def get_all(self, page: int, page_size: int) -> tuple[list[T], int]:
        """Returns (items, total_count)."""
        ...

    async def add(self, record: T) -> T:
        """Takes and returns the SAME plain-data shape (T), never the
        ORM model directly."""
        ...

    async def update(self, id: int, record: T) -> T: ...

    async def delete(self, id: int) -> None: ...


class VenueLookup(Protocol):
    """
    Deliberately NOT `Repository[VenueRecord]`.

    EventService needs to answer one question — "does this venue
    exist?" — and nothing else about venues. Giving it the full
    Repository[VenueRecord] (add/update/delete included) would let event
    creation accidentally depend on, or be coupled to, venue management
    concerns it has no business touching. This is the Interface
    Segregation Principle: depend on the narrowest interface that
    satisfies what you actually need, not the biggest one that happens
    to have the method somewhere in it.

    SqlVenueRepository (below) can still implement the full
    Repository[VenueRecord] for whatever venue-management routes exist
    elsewhere — it just also happens to satisfy this narrower Protocol
    structurally, for free.
    """

    async def get(self, id: int) -> VenueRecord: ...
