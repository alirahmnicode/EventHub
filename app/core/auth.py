from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request, status
from jwt.exceptions import DecodeError, InvalidSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.engine import get_db
from app.models.user import User

ph = PasswordHasher()


settings = get_settings()

AUTH_JWT_SECRET_KEY = settings.auth.jwt_private_key_path.read_text()
AUTH_JWT_PUBLIC_KEY = settings.auth.jwt_public_key_path.read_text()
ALGORITHM = settings.auth.jwt_algorithm
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth.jwt_access_token_expire_minutes
AUTH_REFRESH_TOKEN_EXPIRE_DAYS = settings.auth.jwt_refresh_token_expire_days


def get_hashed_password(plain_password: str) -> str:
    return ph.hash(password=plain_password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    return ph.verify(hash=hashed_password, password=plain_password)


def generate_access_token(user_id: int) -> str:
    # generate access toke with Private key

    now = datetime.now(UTC)
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=AUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload,
        AUTH_JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def generate_refresh_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=AUTH_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(
        payload,
        AUTH_JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_refresh_token(token):
    try:
        decoded = jwt.decode(token, AUTH_JWT_PUBLIC_KEY, algorithms=ALGORITHM)
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, user_id not in the payload",
            )

        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token type not valid",
            )
        if datetime.now() > datetime.fromtimestamp(decoded.get("exp")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token expired",
            )
        return user_id

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, decode failed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed, {e}",
        )


# ------------------------------------------------------------------------------------------
# dependencies
# ------------------------------------------------------------------------------------------


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    try:
        decoded = jwt.decode(access_token, AUTH_JWT_PUBLIC_KEY, algorithms=ALGORITHM)
        user_id = decoded.get("user_id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, user_id not in the payload",
            )

        if decoded.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token type not valid",
            )
        if datetime.now() > datetime.fromtimestamp(decoded.get("exp")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token expired",
            )

        user_obj = await db.execute(select(User).where(User.id == user_id))
        return user_obj.scalar_one_or_none()

    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, invalid signature",
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed, decode failed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed, {e}",
        )


def require_role(role: str = "admin"):
    def checker(user=Depends(get_current_user)):
        if user.role.name != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "insufficient_role"},
            )
        return user

    return checker
