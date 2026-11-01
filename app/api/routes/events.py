from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentAdmin, EventServiceDep, Limit, Offset, SessionDep
from app.models import Event
from app.schemas import EventCreate, EventDetail, EventRead, EventUpdate
from app.utils import or_404, remove_or_409

router = APIRouter(prefix="/events", tags=["events"])


async def _require_venue(db: SessionDep, venue_id: int) -> None:
    or_404(await crud.venue.get(db, venue_id), "Venue")


@router.post("", response_model=EventRead, status_code=201)
async def create_event(body: EventCreate, db: SessionDep, admin: CurrentAdmin):
    await _require_venue(db, body.venue_id)
    # status defaults to "draft"; publish with PATCH once ticket types exist
    return await crud.event.create(db, body, created_by=admin.id)


# event_status: Annotated[EventStatus | None, Query(alias="status")] = None,
@router.get("", response_model=list[EventRead])
async def list_events(
    service: EventServiceDep,
    venue_id: int | None = None,
    offset: Offset = 0,
    limit: Limit = 20,
):
    return await service.list_events(
        venue_id=venue_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(event_id: int, service: EventServiceDep):
    return await service.get_event(event_id=event_id)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int, body: EventUpdate, service: EventServiceDep, admin: CurrentAdmin
):
    return await service.update_event(event_id=event_id, data=body, user=admin)


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: int, service: EventServiceDep, admin: CurrentAdmin):
    return await service.delete_event(event_id=event_id, user=admin)
