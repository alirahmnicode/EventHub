from math import ceil
from typing import TypeVar
from urllib.parse import urlencode

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from app.schemas.pagination import PaginatedResponse, PaginationLinks

T = TypeVar("T")


async def paginate(
    *,
    entity,
    query: Query,
    schema: type[T],
    request: Request,
    db: AsyncSession,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    # Total number of records
    count_query = select(func.count()).select_from(entity)

    # If the original query has filters, preserve them
    count_query = query.with_only_columns(
        func.count(),
        maintain_column_froms=True,
    )

    result = await db.execute(count_query)
    total = result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()
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
