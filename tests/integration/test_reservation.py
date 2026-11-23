"""Concurrency tests for ReservationService against a real Postgres.

SQLite can't be used: it ignores SELECT ... FOR UPDATE and doesn't give real
concurrent transactions, so an oversell bug would go unnoticed.

Run:
    docker run --rm -e POSTGRES_PASSWORD=test -p 5433:5432 postgres:16
    export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres
    pytest tests/test_reservation_concurrency.py -v

Needs: pytest, pytest-asyncio, asyncpg.
"""

import asyncio
import os
import random

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.reservation import Reservation
from app.models.ticket_type import TicketType
from app.models.user import User
from app.repositories.reservation import ReservationRepository
from app.services.exceptions import InsufficientInventoryError
from app.services.reservation import ReservationService

TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
MAX_CONCURRENCY = 60  # keep below Postgres max_connections (default 100)

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not TEST_DB_URL, reason="TEST_DATABASE_URL not set"),
]


# ---- fixtures / helpers -----------------------------------------------------


@pytest_asyncio.fixture
async def session_factory():
    # One pooled connection per concurrent "user", so they truly overlap.
    engine = create_async_engine(TEST_DB_URL, pool_size=MAX_CONCURRENCY, max_overflow=0)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def seed(session_factory, *, total: int, n_users: int):
    """Create n users and one ticket type with `total` tickets."""
    async with session_factory() as session:
        users = [
            User(email=f"user{i}@test.dev")  # adjust to your User model
            for i in range(n_users)
        ]
        ticket_type = TicketType(
            name="Scarce",
            total_quantity=total,  # adjust to your model
        )
        session.add_all([*users, ticket_type])
        await session.commit()
        return [u.id for u in users], ticket_type.id


async def run_concurrently(session_factory, calls: list[dict]):
    """Fire ReservationService.create(**call) for every call at once.

    Each call gets its own session (= its own DB connection/transaction),
    exactly like separate HTTP requests. Returns a Reservation or the raised
    exception for each call, in order.
    """
    gate = asyncio.Event()

    async def one(kwargs: dict):
        async with session_factory() as session:
            service = ReservationService(ReservationRepository(session))
            await gate.wait()
            return await service.create(**kwargs)

    tasks = [asyncio.create_task(one(c)) for c in calls]
    await asyncio.sleep(0.1)  # let every task park at the gate
    gate.set()
    return await asyncio.gather(*tasks, return_exceptions=True)


async def db_totals(session_factory, ticket_type_id: int) -> tuple[int, int]:
    """(sum of quantity, number of rows) actually stored for the ticket type."""
    async with session_factory() as session:
        row = (
            await session.execute(
                select(
                    func.coalesce(func.sum(Reservation.quantity), 0),
                    func.count(Reservation.id),
                ).where(Reservation.ticket_type_id == ticket_type_id)
            )
        ).one()
    return int(row[0]), int(row[1])


# ---- tests ------------------------------------------------------------------


@pytest.mark.parametrize(
    "total,n_users,max_qty",
    [
        (1, 50, 1),  # last-ticket race
        (10, 50, 1),  # heavy contention, uniform size
        (25, 50, 3),  # mixed sizes: 2 or 3 can fail while 1 still fits
    ],
)
async def test_never_oversells(session_factory, total, n_users, max_qty):
    rng = random.Random(42)
    quantities = [rng.randint(1, max_qty) for _ in range(n_users)]
    user_ids, ticket_type_id = await seed(session_factory, total=total, n_users=n_users)

    calls = [
        {
            "user_id": uid,
            "ticket_type_id": ticket_type_id,
            "quantity": qty,
            "idempotency_key": f"key-{uid}",  # every user has a unique key
        }
        for uid, qty in zip(user_ids, quantities)
    ]
    results = await run_concurrently(session_factory, calls)

    # Only two outcomes are legitimate; anything else (deadlock, constraint
    # error, ...) is a bug.
    for result in results:
        assert isinstance(result, (Reservation, InsufficientInventoryError)), repr(
            result
        )

    accepted = [(c, r) for c, r in zip(calls, results) if isinstance(r, Reservation)]
    rejected = [
        (c, r) for c, r in zip(calls, results) if not isinstance(r, Reservation)
    ]
    sold = sum(c["quantity"] for c, _ in accepted)

    # 1. The invariant: never sell more than exists.
    assert sold <= total

    # 2. What clients were told matches what the DB stored.
    db_sold, db_rows = await db_totals(session_factory, ticket_type_id)
    assert db_sold == sold
    assert db_rows == len(accepted)

    # 3. No false rejections: every rejected request really didn't fit.
    #    (Stock only shrinks in this test, so what was left at rejection time
    #    is at least what is left now.)
    for call, _ in rejected:
        assert total - sold < call["quantity"]


async def test_same_idempotency_key_concurrently_creates_one_reservation(
    session_factory,
):
    (user_id,), ticket_type_id = await seed(session_factory, total=100, n_users=1)
    call = {
        "user_id": user_id,
        "ticket_type_id": ticket_type_id,
        "quantity": 2,
        "idempotency_key": "same-key",
    }
    results = await run_concurrently(session_factory, [call] * 30)

    for result in results:
        assert isinstance(result, Reservation), repr(result)

    # Every retry got the same reservation back...
    assert len({r.id for r in results}) == 1

    # ...and only one row exists, holding only 2 tickets.
    assert await db_totals(session_factory, ticket_type_id) == (2, 1)
