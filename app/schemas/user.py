from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)


# ---------- Input schemas ----------


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=128, examples=["admin123"])

    # @field_validator("password")
    # @classmethod
    # def password_complexity(cls, v: str) -> str:
    #     if not any(c.isdigit() for c in v):
    #         raise ValueError("password must contain at least one digit")
    #     if not any(c.isupper() for c in v):
    #         raise ValueError("password must contain at least one uppercase letter")
    #     return v


class UserLogin(BaseModel):
    email: EmailStr = Field(examples=["admin@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["admin123"])


class UserUpdate(BaseModel):
    """Partial update — all fields optional."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)


# ---------- Output schema ----------


class UserRead(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Admin-only variants ----------


class UserRoleUpdate(BaseModel):
    """Used by an admin-only endpoint to change someone's role."""

    role: UserRole
