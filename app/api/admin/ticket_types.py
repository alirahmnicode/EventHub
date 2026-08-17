from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.paginator import PaginatedResponse, paginate
from app.db.engine import get_db
from app.models.ticket_type import TicketType
from app.models.user import User
from app.schemas.ticket_type import (
    TicketTypeCreateSchema,
    TicketTypeReadSchema,
    TicketTypeUpdateSchema,
)

router = APIRouter(
    prefix="/admin/ticket-types",
    tags=["Admin Ticket Types"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketTypeReadSchema,
)
async def create_ticket_type(
    payload: TicketTypeCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    ticket_type = TicketType(**payload.model_dump())

    db.add(ticket_type)
    await db.commit()
    await db.refresh(ticket_type)

    return ticket_type


@router.get(
    "/",
    response_model=PaginatedResponse[TicketTypeReadSchema],
)
async def get_ticket_types(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    query = select(TicketType)

    return await paginate(
        entity=TicketType,
        query=query,
        schema=TicketTypeReadSchema,
        db=db,
        request=request,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{ticket_type_id}",
    response_model=TicketTypeReadSchema,
)
async def get_ticket_type(
    ticket_type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(TicketType).where(TicketType.id == ticket_type_id))

    ticket_type = result.scalar_one_or_none()

    if ticket_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )

    return ticket_type


@router.patch(
    "/{ticket_type_id}",
    response_model=TicketTypeReadSchema,
)
async def update_ticket_type(
    ticket_type_id: int,
    payload: TicketTypeUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(TicketType).where(TicketType.id == ticket_type_id))

    ticket_type = result.scalar_one_or_none()

    if ticket_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(ticket_type, field, value)

    await db.commit()
    await db.refresh(ticket_type)

    return ticket_type


@router.delete(
    "/{ticket_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_ticket_type(
    ticket_type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(TicketType).where(TicketType.id == ticket_type_id))

    ticket_type = result.scalar_one_or_none()

    if ticket_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )

    await db.delete(ticket_type)
    await db.commit()

    return None
