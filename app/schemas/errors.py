from typing import Any

from pydantic import BaseModel


class ErrorSchema(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponseSchema(BaseModel):
    error: ErrorSchema
