from math import ceil
from typing import TypeVar
from urllib.parse import urlencode

from fastapi import Request

from app.schemas.pagination import PaginatedResponse, PaginationLinks

T = TypeVar("T")


async def paginate(
    total: int,
    items,
    schema: type[T],
    request: Request,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    offset = (page - 1) * page_size
    results = [schema.model_validate(item) for item in items]

    base_url = str(request.url).split("?")[0]
    query_params = dict(request.query_params)
    query_params["page_size"] = str(page_size)

    next_url = previous_url = None

    if offset + page_size < total:
        query_params["page"] = str(page + 1)
        next_url = f"{base_url}?{urlencode(query_params)}"

    if page > 1:
        query_params["page"] = str(page - 1)
        previous_url = f"{base_url}?{urlencode(query_params)}"

    return PaginatedResponse[T](
        links=PaginationLinks(next=next_url, previous=previous_url, current=page),
        total_items=total,
        total_pages=ceil(total / page_size),
        results=results,
    )
