import pytest

from app.models.user import User, UserRole  # ADAPT
from app.models.venue import Venue  # ADAPT
from app.repositories.venue import VenueRepository
from app.schemas.venue import VenueCreate, VenueUpdate
from app.services.venue import VenueService

# ---------- model factories (unchanged) ----------


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
def make_venue():
    def _make(id: int = 1, **extra) -> Venue:
        defaults = {"name": f"Venue {id}", "city": "Berlin"}  # ADAPT
        return Venue(id=id, **{**defaults, **extra})

    return _make


@pytest.fixture
def regular_user(make_user) -> User:
    return make_user(id=2, role=UserRole.CUSTOMER)


@pytest.fixture
def admin(make_user) -> User:
    return make_user(id=99, role=UserRole.ADMIN)


@pytest.fixture
def venue(make_venue) -> Venue:
    return make_venue(id=1)


@pytest.fixture
def venue_create() -> VenueCreate:
    return VenueCreate(name="New Hall", city="Hamburg", address="test", capacity=21)


@pytest.fixture
def venue_update() -> VenueUpdate:
    return VenueUpdate(name="Renamed Hall")  # ADAPT


# ---------- mocked repository ----------


@pytest.fixture
def repo(mocker, venue):
    repo = mocker.create_autospec(VenueRepository, instance=True, spec_set=True)
    repo.get.return_value = venue
    repo.get_list.return_value = [venue]
    return repo


@pytest.fixture
def service(repo) -> VenueService:
    return VenueService(repo)
