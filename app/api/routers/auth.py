import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    generate_access_token,
    generate_refresh_token,
    get_hashed_password,
    require_role,
    verify_password,
)
from app.core.config import Settings, get_settings
from app.db.engine import get_db
from app.models import User
from app.schemas.user import UserLogin, UserRegister

settings: Settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).where(User.email == payload.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user already exist with this email.",
        )

    user = User(email=payload.email, full_name=payload.full_name)
    user.hashed_password = get_hashed_password(payload.password)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "user_id": user.id,
        "email": user.email,
    }


@router.post("/login")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).where(User.email == payload.email))
    user_obj = existing_user.scalar_one_or_none()

    if user_obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User dose not exist with this email.",
        )

    if not verify_password(
        hashed_password=user_obj.hashed_password, plain_password=payload.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credential.",
        )

    access_token = generate_access_token(str(user_obj.id))
    refresh_token = generate_refresh_token(str(user_obj.id))

    response = JSONResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
        status_code=status.HTTP_200_OK,
    )
    csrf_token = secrets.token_urlsafe(32)

    # Set the tokens in the cookies
    response.set_cookie(
        "access_token",
        access_token,
        httponly=settings.cookie.AUTH_COOKIE_HTTPONLY,
        secure=settings.cookie.AUTH_COOKIE_SECURE,
        samesite=settings.cookie.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=settings.cookie.AUTH_COOKIE_HTTPONLY,
        secure=settings.cookie.AUTH_COOKIE_SECURE,
        samesite=settings.cookie.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=False,
        secure=settings.cookie.AUTH_COOKIE_SECURE,
        samesite=settings.cookie.AUTH_COOKIE_SAMESITE,
    )
    response.set_cookie(
        key="sid",
        value=str(uuid.uuid4()),
        httponly=settings.cookie.AUTH_COOKIE_HTTPONLY,
        secure=settings.cookie.AUTH_COOKIE_SECURE,
        samesite=settings.cookie.AUTH_COOKIE_SAMESITE,
    )

    return response


@router.get("/admin")
async def get_admin(
    admin: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_db)
):
    pass
