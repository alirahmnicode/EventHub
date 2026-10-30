from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.settings import settings


async def ensure_test_database() -> None:
    url = make_url(str(settings.SQLALCHEMY_TEST_DATABASE_URI))
    db_name = url.database
    assert db_name.endswith("_test"), f"Refusing to create {db_name}"

    admin_engine = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",  # CREATE DATABASE can't run in a transaction
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin_engine.dispose()
