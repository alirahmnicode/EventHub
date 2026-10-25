from app.schemas.base import ORMModel
from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    partner_name: str = Field(min_length=1, max_length=200)
    scopes: list[str] = Field(default_factory=list)
    rate_limit_tier: str = Field(default="standard", max_length=50)


class ApiKeyUpdate(BaseModel):
    partner_name: str | None = Field(default=None, min_length=1, max_length=200)
    scopes: list[str] | None = None
    rate_limit_tier: str | None = Field(default=None, max_length=50)


class ApiKeyRead(ORMModel):
    id: int
    partner_name: str
    scopes: list[str]
    rate_limit_tier: str
    # key_hash is intentionally absent.


class ApiKeyCreated(ApiKeyRead):
    """Returned once, at creation. The raw key cannot be recovered later."""

    api_key: str
