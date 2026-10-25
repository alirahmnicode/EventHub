from typing import Any

from app.schemas.base import ORMModel
from pydantic import BaseModel, Field


class FeatureFlagBase(BaseModel):
    enabled: bool = False
    rollout: dict[str, Any] | None = None


class FeatureFlagCreate(FeatureFlagBase):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9_.-]*$")


class FeatureFlagUpdate(BaseModel):
    enabled: bool | None = None
    rollout: dict[str, Any] | None = None


class FeatureFlagRead(ORMModel, FeatureFlagBase):
    id: int
    key: str
