from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.schemas.base import ORMModel


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        # The DB unique index is case-sensitive, so normalize here.
        return v.lower()


class UserRegister(UserBase):
    """Public sign-up. Role is NOT accepted from clients."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """Self-service profile update."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str | None) -> str | None:
        return v.lower() if v else v


class UserRoleUpdate(BaseModel):
    """Admin-only."""

    role: UserRole


class UserRead(ORMModel, UserBase):
    id: int
    role: UserRole
    created_at: datetime
    # hashed_password is intentionally absent.


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None


class NewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
