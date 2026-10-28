"""Seed the database with sample data.

Run from the project root (inside the container):

    python -m app.db.init_data

Safe to run repeatedly: every row is looked up first and only created if missing.

To seed a new model:
  1. Add `async def seed_<model>(session, ctx)` below (copy `seed_venues`).
  2. Append it to SEEDERS, after any seeder whose rows it depends on.
"""

import asyncio
import hashlib
import os
import secrets
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.base import SessionLocal, engine
from app.models import Event, User, Venue
from app.models.enums import EventStatus, UserRole

M = TypeVar("M")
Context = dict[str, Any]  # rows created by earlier seeders, for later ones to use
Seeder = Callable[[AsyncSession, Context], Awaitable[None]]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
async def get_or_create[M](
    session: AsyncSession,
    model: type[M],
    lookup: dict[str, Any],
    defaults: dict[str, Any] | None = None,
) -> tuple[M, bool]:
    """Return (row, created). `lookup` identifies the row; `defaults` fills the rest."""
    instance = await session.scalar(select(model).filter_by(**lookup))
    if instance is not None:
        return instance, False
    instance = model(**lookup, **(defaults or {}))
    session.add(instance)
    await session.flush()  # assigns the id without committing
    return instance, True


def hash_password(password: str) -> str:
    """Stdlib scrypt, so seeding needs no extra dependency.

    Replace with the hasher your auth code uses (argon2/bcrypt) once you add
    login, otherwise these seeded users won't be able to sign in.
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _report(name: str, created: int, total: int) -> None:
    print(f"  {name}: {created} created, {total - created} already existed")


# --------------------------------------------------------------------------- #
# Seed data
# --------------------------------------------------------------------------- #
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "password123")  # dev only

USERS = [
    {
        "email": "admin@gmail.local",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "admin@eventhub.local",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "customer@eventhub.local",
        "full_name": "Test Customer",
        "role": UserRole.CUSTOMER,
    },
]

VENUES = [
    {
        "name": "Spree Arena",
        "address": "Example Str. 1",
        "city": "Berlin",
        "capacity": 12000,
    },
    {
        "name": "Elbe Concert Hall",
        "address": "Example Allee 22",
        "city": "Hamburg",
        "capacity": 2100,
    },
    {
        "name": "Isar Club",
        "address": "Example Platz 5",
        "city": "Munich",
        "capacity": 450,
    },
]

# days_from_now / hours are relative to the moment you run the script.
EVENTS = [
    {
        "venue": "Spree Arena",
        "title": "Summer Music Festival",
        "description": "Two stages, ten bands, one long night.",
        "days_from_now": 30,
        "hours": 8,
        "status": EventStatus.PUBLISHED,
    },
    {
        "venue": "Spree Arena",
        "title": "Tech Conference 2027",
        "description": "Talks and workshops on software and AI.",
        "days_from_now": 60,
        "hours": 9,
        "status": EventStatus.PUBLISHED,
    },
    {
        "venue": "Elbe Concert Hall",
        "title": "Classical Evening",
        "description": "Symphony orchestra performing a mixed program.",
        "days_from_now": 14,
        "hours": 3,
        "status": EventStatus.PUBLISHED,
    },
    {
        "venue": "Isar Club",
        "title": "Indie Night",
        "description": "Local bands, small room, loud speakers.",
        "days_from_now": 7,
        "hours": 5,
        "status": EventStatus.DRAFT,
    },
    {
        "venue": "Isar Club",
        "title": "Comedy Open Mic (cancelled)",
        "description": "Cancelled due to scheduling conflict.",
        "days_from_now": 21,
        "hours": 3,
        "status": EventStatus.CANCELLED,
    },
    {
        "venue": "Isar Club",
        "title": "Comedy Open Mic",
        "description": "Cancelled due to scheduling conflict.",
        "days_from_now": 21,
        "hours": 3,
        "status": EventStatus.PUBLISHED,
    },
]


# --------------------------------------------------------------------------- #
# One seeder per model. Each stores its rows in ctx for later seeders.
# --------------------------------------------------------------------------- #
async def seed_users(session: AsyncSession, ctx: Context) -> None:
    ctx["users"] = {}
    created = 0
    for data in USERS:
        user, was_created = await get_or_create(
            session,
            User,
            lookup={"email": data["email"]},
            defaults={
                "full_name": data["full_name"],
                "role": data["role"],
                "hashed_password": get_password_hash(SEED_PASSWORD),
            },
        )
        ctx["users"][user.email] = user
        created += was_created
    _report("users", created, len(USERS))


async def seed_venues(session: AsyncSession, ctx: Context) -> None:
    admin = ctx["users"]["admin@eventhub.local"]
    ctx["venues"] = {}
    created = 0
    for data in VENUES:
        venue, was_created = await get_or_create(
            session,
            Venue,
            lookup={"name": data["name"]},
            defaults={
                "address": data["address"],
                "city": data["city"],
                "capacity": data["capacity"],
                "created_by": admin.id,
            },
        )
        ctx["venues"][venue.name] = venue
        created += was_created
    _report("venues", created, len(VENUES))


async def seed_events(session: AsyncSession, ctx: Context) -> None:
    admin = ctx["users"]["admin@eventhub.local"]
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    ctx["events"] = {}
    created = 0
    for data in EVENTS:
        venue = ctx["venues"][data["venue"]]
        starts_at = now + timedelta(days=data["days_from_now"])
        event, was_created = await get_or_create(
            session,
            Event,
            lookup={"title": data["title"], "venue_id": venue.id},
            defaults={
                "description": data["description"],
                "starts_at": starts_at,
                "ends_at": starts_at + timedelta(hours=data["hours"]),
                "status": data["status"],
                "created_by": admin.id,
            },
        )
        ctx["events"][event.title] = event
        created += was_created
    _report("events", created, len(EVENTS))


# Order matters: a seeder must come after the ones whose rows it needs.
SEEDERS: list[Seeder] = [
    seed_users,
    seed_venues,
    seed_events,
]


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
async def init_data() -> None:
    ctx: Context = {}
    async with SessionLocal() as session:
        print("Seeding database...")
        for seeder in SEEDERS:
            await seeder(session, ctx)
        await session.commit()  # all-or-nothing: an error above rolls everything back
    print("Done.")


async def main() -> None:
    try:
        await init_data()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
