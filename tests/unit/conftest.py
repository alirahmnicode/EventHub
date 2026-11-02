from datetime import datetime, timezone

import pytest

from app.models import Event, TicketType, User, Venue
from app.models.enums import EventStatus, UserRole
from app.schemas import (
    EventCreate,
    EventUpdate,
    TicketTypeCreate,
    TicketTypeUpdate,
    VenueCreate,
    VenueUpdate,
)

STARTS_AT = datetime(2030, 1, 1, 18, 0, tzinfo=timezone.utc)
ENDS_AT = datetime(2030, 1, 1, 22, 0, tzinfo=timezone.utc)
SALES_START = datetime(2029, 12, 1, 9, 0, tzinfo=timezone.utc)
SALES_END = datetime(2029, 12, 31, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def make_repo(mocker):
    """make_repo(SomeRepository) -> autospecced async-aware mock.
    Wrong method names or wrong arguments fail the test."""

    def _make(repo_cls):
        return mocker.create_autospec(repo_cls, instance=True, spec_set=True)

    return _make


# ---------- users ----------


@pytest.fixture
def make_user():
    def _make(id: int = 1, role: UserRole = UserRole.CUSTOMER, **extra) -> User:
        return User(
            id=id,
            email=f"user{id}@test.com",
            hashed_password="not-a-real-hash",
            role=role,
            **extra,
        )

    return _make


@pytest.fixture
def regular_user(make_user) -> User:
    return make_user(id=2, role=UserRole.CUSTOMER)


@pytest.fixture
def admin(make_user) -> User:
    return make_user(id=99, role=UserRole.ADMIN)


# ---------- venues ----------


@pytest.fixture
def make_venue():
    def _make(id: int = 1, **extra) -> Venue:
        defaults = {"name": f"Venue {id}", "city": "Berlin"}  # ADAPT
        return Venue(id=id, **{**defaults, **extra})

    return _make


@pytest.fixture
def venue(make_venue) -> Venue:
    return make_venue(id=1)


@pytest.fixture
def venue_create() -> VenueCreate:
    return VenueCreate(name="New Hall", city="Hamburg", address="test", capacity=21)


@pytest.fixture
def venue_update() -> VenueUpdate:
    return VenueUpdate(name="Renamed Hall")


# ---------- events ----------


@pytest.fixture
def make_event():
    def _make(id: int = 1, **extra) -> Event:
        defaults = {  # ADAPT to your columns
            "title": f"Event {id}",
            "venue_id": 1,
            "status": EventStatus.PUBLISHED,
            "starts_at": STARTS_AT,
            "ends_at": ENDS_AT,
        }
        return Event(id=id, **{**defaults, **extra})

    return _make


@pytest.fixture
def make_event_create():
    def _make(**overrides) -> EventCreate:
        defaults = {  # ADAPT
            "title": "New Event",
            "venue_id": 1,
            "starts_at": STARTS_AT,
            "ends_at": ENDS_AT,
        }
        return EventCreate(**{**defaults, **overrides})

    return _make


@pytest.fixture
def make_event_update():
    def _make(**fields) -> EventUpdate:
        return EventUpdate(**fields)

    return _make


# ---------- ticket types ----------


@pytest.fixture
def make_ticket_type():
    def _make(id: int = 1, **extra) -> TicketType:
        defaults = {
            "event_id": 1,
            "name": f"Ticket {id}",
            "price_cents": 5000,
            "currency": "USD",
            "total_quantity": 100,
            # Column defaults only apply on flush, so set these explicitly:
            "reserved_quantity": 0,
            "sold_quantity": 0,
            "sales_start_at": SALES_START,
            "sales_end_at": SALES_END,
        }
        return TicketType(id=id, **{**defaults, **extra})

    return _make


@pytest.fixture
def make_ticket_type_create():
    def _make(*, validate: bool = True, **overrides) -> TicketTypeCreate:
        defaults = {
            "event_id": 1,
            "name": "General",
            "price_cents": 5000,
            "total_quantity": 100,
            "sales_start_at": SALES_START,
            "sales_end_at": SALES_END,
        }
        values = {**defaults, **overrides}
        if validate:
            return TicketTypeCreate(**values)
        return TicketTypeCreate.model_construct(**values)  # skips the schema validator

    return _make


@pytest.fixture
def make_ticket_type_update():
    def _make(**fields) -> TicketTypeUpdate:
        return TicketTypeUpdate(**fields)  # model_fields_set = exactly the keys passed

    return _make
