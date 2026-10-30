import random
import string

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.core.settings import settings
from app.crud import user_crud
from app.models import User
from app.schemas.user import UserRegister, UserUpdate


def random_lower_string(k: int = 32) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=k))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


async def get_superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


async def user_authentication_headers(
    *, client: AsyncClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}
    r = await client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    r.raise_for_status()
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


async def create_random_user(db: AsyncSession) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserRegister(email=email, password=get_password_hash(password))
    user = await user_crud.create_user(session=db, user_create=user_in)
    return user


async def authentication_token_from_email(
    *, client: AsyncClient, email: str, db: AsyncSession
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    # username and password for creating new user
    password = random_lower_string()

    user = await user_crud.get_user_by_email(session=db, email=email)
    if not user:
        user_in_create = UserRegister(email=email, password=password)
        user = await user_crud.create_user(session=db, user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        if not user.id:
            raise Exception("User id not set")
        user = await user_crud.update_user(
            session=db, db_user=user, user_in=user_in_update
        )

    return await user_authentication_headers(
        client=client, email=email, password=password
    )
