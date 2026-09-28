from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.paginator import PaginatedResponse, paginate
from app.db.engine import get_db
from app.models import User
from app.repositories.interfaces import (
    NotFoundError,
)
from app.repositories.sql import SqlEventRepository
from app.repositories.venue_sql import SqlVenueRepository
from app.schemas.event import EventCreateSchema, EventReadSchema, EventUpdateSchema
from app.services.event import (
    CannotDeletePublishedEventError,
    EventService,
    InvalidEventTimesError,
    InvalidStatusTransitionError,
)

router = APIRouter(prefix="/admin", tags=["Admin Events"])


async def get_event_service(db: AsyncSession = Depends(get_db)):
    event_repository = SqlEventRepository(db)
    venue_lookup = SqlVenueRepository(db)
    return EventService(event_repository, venue_lookup)


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    response_model=EventReadSchema,
)
async def create_event(
    payload: EventCreateSchema,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        event = await service.create_event(data=payload, created_by=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return event


@router.get(
    "/events/{event_id}",
    response_model=EventReadSchema,
)
async def get_event(
    event_id: int,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        event = await service.get_event(event_id)
        return event
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/events",
    response_model=PaginatedResponse[EventReadSchema],
)
async def list_events(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        events, total_count = await service.list_events(page=page, page_size=page_size)
        return await paginate(
            total_count, events, EventReadSchema, request, page, page_size
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/events/{event_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EventReadSchema,
)
async def update_event(
    event_id: int,
    payload: EventUpdateSchema,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        event = await service.update_event(event_id, payload)
        return event
    except InvalidEventTimesError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    "/events/{event_id}/status",
    response_model=EventReadSchema,
)
async def change_event_status(
    event_id: int,
    new_status: str,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        event = await service.change_status(event_id, new_status)
        return event
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    event_id: int,
    service: EventService = Depends(get_event_service),
    current_user: User = Depends(require_role("admin")),
):
    try:
        await service.delete_event(event_id)
    except CannotDeletePublishedEventError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
