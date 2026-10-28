import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserRegister, UserUpdate


async def create_user(*, session: AsyncSession, user_create: UserRegister) -> User:
    # hashing is CPU-heavy, so run it in a thread to avoid blocking the event loop
    hashed_password = get_password_hash(user_create.password)

    db_obj = User(
        **user_create.model_dump(exclude={"password"}),
        hashed_password=hashed_password,
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_user(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)

    password = user_data.pop("password", None)
    if password:
        user_data["hashed_password"] = get_password_hash(password)

    for field, value in user_data.items():
        setattr(db_user, field, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def get_user_by_username(*, session: AsyncSession, username: str) -> User | None:
    return await session.scalar(select(User).where(User.username == username))


async def get_user_by_username_or_email(
    *, session: AsyncSession, username: str, email: str
) -> User | None:
    user_by_email = await get_user_by_email(session=session, email=email)
    user_by_username = await get_user_by_username(session=session, username=username)

    return user_by_email or user_by_username


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


from fastapi.concurrency import run_in_threadpool


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        await run_in_threadpool(verify_password, password, DUMMY_HASH)
        return None

    verified, new_hash = await run_in_threadpool(
        verify_password, password, db_user.hashed_password
    )

    if not verified:
        return None

    if new_hash:
        db_user.hashed_password = new_hash
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    return db_user
