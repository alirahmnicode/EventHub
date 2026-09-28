from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.auth import get_hashed_password
from app.db.engine import Base, get_db
from app.main import app
from app.models import Event, EventStatus, TicketType, User, Venue
from app.models.enums import UserRole
from app.repositories.sql import SqlEventRepository
from app.repositories.venue_sql import SqlVenueRepository
from app.services.event import EventService

# from app.models.user import User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="package")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="package")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="package")
async def admin_user(db_session: AsyncSession) -> User:
    """Seed an admin user in the test DB so auth_client can log in as them."""
    user = User(
        email="admin@example.com",
        hashed_password=get_hashed_password("admin123"),
        full_name="Test Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


@pytest_asyncio.fixture(scope="package")
async def customer_user(db_session: AsyncSession) -> User:
    """Seed an customer user in the test DB so auth_client can log in as them."""
    user = User(
        email=fake.email(),
        hashed_password=get_hashed_password("admin123"),
        full_name=fake.name(),
        role=UserRole.customer,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, admin_user: User):
    response = await client.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest_asyncio.fixture
async def unauth_client(client: AsyncClient):

    client.headers.update({"Authorization": ""})
    return client


@pytest_asyncio.fixture
async def customer(client: AsyncClient, customer_user: User):
    response = await client.post(
        "/auth/login",
        json={"email": customer_user.email, "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    client.headers.update({"Authorization": ""})
    return client


@pytest_asyncio.fixture(scope="package")
async def client(test_engine, db_session):
    """HTTP client with the app's DB dependency overridden to use the test engine."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # app.dependency_overrides[get_event_service] = event_service
    # app.dependency_overrides[require_role] = override_require_role

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    # app.dependency_overrides.pop(get_event_service, None)
    # app.dependency_overrides.pop(require_role, None)


fake = Faker()


@pytest.fixture
async def make_user(db_session):
    """Factory fixture: persists a User row. Usage: user = make_user(role=UserRole.organizer)"""

    async def _make_user(**overrides):
        defaults = {
            "email": fake.email(),
            "hashed_password": get_hashed_password(fake.password(length=8)),
            "full_name": fake.name(),
            "role": UserRole.customer,
        }
        defaults.update(overrides)
        user = User(**defaults)
        db_session.add(user)
        await db_session.flush()
        return user

    return _make_user


@pytest.fixture
async def make_venue(db_session, make_user):
    async def _make_venue(**overrides):
        creator = overrides.pop("creator", None) or await make_user(role=UserRole.admin)
        defaults = {
            "name": fake.company() + " Hall",
            "address": fake.street_address(),
            "city": fake.city(),
            "capacity": fake.random_int(min=50, max=5000),
            "created_by": creator.id,
        }
        defaults.update(overrides)
        venue = Venue(**defaults)
        db_session.add(venue)
        await db_session.flush()
        return venue

    return _make_venue


@pytest.fixture
async def make_event(db_session, make_venue, make_user):
    async def _make_event(**overrides):
        creator = overrides.pop("creator", None) or await make_user(
            role=UserRole.customer
        )
        venue = overrides.pop("venue", None) or await make_venue(creator=creator)
        starts_at = overrides.pop(
            "starts_at", datetime.now(timezone.utc) + timedelta(days=30)
        )
        ends_at = overrides.pop("ends_at", starts_at + timedelta(hours=3))

        defaults = {
            "venue_id": venue.id,
            "title": fake.sentence(nb_words=4).rstrip("."),
            "description": fake.paragraph(),
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": EventStatus.draft,
            "created_by": creator.id,
        }
        defaults.update(overrides)
        event = Event(**defaults)
        db_session.add(event)
        await db_session.flush()
        return event

    return _make_event


@pytest.fixture
async def make_ticket_type(db_session, make_event):
    async def _make_ticket_type(**overrides):
        event = overrides.pop("event", None) or await make_event()
        defaults = {
            "event_id": event.id,
            "name": fake.random_element(["General Admission", "VIP", "Early Bird"]),
            "price_cents": fake.random_int(min=1000, max=50000),
            "currency": "USD",
            "total_quantity": fake.random_int(min=50, max=1000),
            "reserved_quantity": 0,
            "sold_quantity": 0,
            "sales_start_at": None,
            "sales_end_at": None,
        }
        defaults.update(overrides)
        tt = TicketType(**defaults)
        db_session.add(tt)
        await db_session.flush()
        return tt

    return _make_ticket_type


@pytest.fixture(autouse=True)
async def mock_data(make_event, make_user, make_venue, make_ticket_type):
    # create admin user
    admin_user = await make_user()

    # create events
    for _ in range(3):
        event = await make_event(creator=admin_user)
        # create ticket types for each event
        for _ in range(2):
            await make_ticket_type(event=event)
