from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationLinks(BaseModel):
    next: str | None
    previous: str | None
    current: int


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    links: PaginationLinks
    total_items: int
    total_pages: int
    results: list[T]
