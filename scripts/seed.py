import asyncio
import random

from faker import Faker

from app.db.database import AsyncSessionLocal
from app.models import Event, Venue

fake = Faker()

NUM_USERS = 10
NUM_VENUES = 5
EVENTS_PER_VENUE = (1, 3)
TICKET_TYPES_PER_EVENT = (2, 4)


async def seed():
    async with AsyncSessionLocal() as session:
        # --- Venues ---
        venues = [
            Venue(
                name=f"{fake.city()} {random.choice(['Arena', 'Hall', 'Theatre', 'Stadium', 'Club'])}",
                city=fake.city(),
                address=fake.street_address(),
                capacity=random.choice([200, 500, 1000, 5000, 20000]),
                created_by=fake.name(),
            )
            for _ in range(NUM_VENUES)
        ]
        session.add_all(venues)
        await session.flush()

        # --- Events ---
        for venue in venues:
            for _ in range(random.randint(*EVENTS_PER_VENUE)):
                event = Event(
                    venue_id=venue.id,
                    title=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=20),
                    starts_at=fake.future_datetime(end_date="+10d"),
                    ends_at=fake.future_datetime(end_date="+90d"),
                    created_by=fake.name(),
                )
                session.add(event)
                await session.flush()

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
