from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.paginator import PaginatedResponse, paginate
from app.db.engine import get_db
from app.models import Event, User, Venue
from app.schemas.event import EventCreateSchema, EventReadSchema, EventUpdateSchema

router = APIRouter(prefix="/admin/events", tags=["Admin Events"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=EventReadSchema,
)
async def create_event(
    payload: EventCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    # Check venue exists
    result = await db.execute(select(Venue).where(Venue.id == payload.venue_id))
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    event = Event(**payload.model_dump())
    event.created_by = current_user.id

    db.add(event)

    await db.commit()
    await db.refresh(event)

    return event


@router.get(
    "/{event_id}",
    response_model=EventReadSchema,
)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@router.get(
    "/",
    response_model=PaginatedResponse[EventReadSchema],
)
async def list_events(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Event).order_by(Event.starts_at)

    return await paginate(
        entity=Event,
        query=query,
        schema=EventReadSchema,
        db=db,
        request=request,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{event_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventReadSchema,
)
async def update_event(
    event_id: int,
    payload: EventUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Check venue if it is being changed
    if "venue_id" in update_data:
        result = await db.execute(
            select(Venue).where(Venue.id == update_data["venue_id"])
        )

        venue = result.scalar_one_or_none()

        if venue is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Venue not found",
            )

    # Calculate final values after the PATCH
    starts_at = update_data.get(
        "starts_at",
        event.starts_at,
    )

    ends_at = update_data.get(
        "ends_at",
        event.ends_at,
    )

    if ends_at <= starts_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ends_at must be after starts_at",
        )

    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    await db.delete(event)
    await db.commit()
