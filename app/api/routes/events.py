from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.api.deps import CurrentAdmin, Limit, Offset, SessionDep
from app.models import Event
from app.models.enums import EventStatus
from app.schemas import EventCreate, EventDetail, EventRead, EventUpdate
from app.utils import or_404, remove_or_409

router = APIRouter(prefix="/events", tags=["events"])


async def _require_venue(db: SessionDep, venue_id: int) -> None:
    or_404(await crud.venue.get(db, venue_id), "Venue")


def _check_dates(event: Event, patch: EventUpdate) -> None:
    """A PATCH may change only one date, so validate against the stored value."""
    starts_at = patch.starts_at or event.starts_at
    ends_at = patch.ends_at or event.ends_at
    if ends_at <= starts_at:
        raise HTTPException(422, "ends_at must be after starts_at")


@router.post("", response_model=EventRead, status_code=201)
async def create_event(body: EventCreate, db: SessionDep, admin: CurrentAdmin):
    await _require_venue(db, body.venue_id)
    # status defaults to "draft"; publish with PATCH once ticket types exist
    return await crud.event.create(db, body, created_by=admin.id)


@router.get("", response_model=list[EventRead])
async def list_events(
    db: SessionDep,
    event_status: Annotated[EventStatus | None, Query(alias="status")] = None,
    venue_id: int | None = None,
    upcoming_only: bool = False,
    offset: Offset = 0,
    limit: Limit = 20,
):
    return await crud.event.search(
        db,
        status=event_status,
        venue_id=venue_id,
        upcoming_only=upcoming_only,
        offset=offset,
        limit=limit,
    )


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(event_id: int, db: SessionDep):
    return or_404(await crud.event.get_with_details(db, event_id), "Event")


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int, body: EventUpdate, db: SessionDep, admin: CurrentAdmin
):
    event = or_404(await crud.event.get(db, event_id), "Event")
    if body.venue_id is not None:
        await _require_venue(db, body.venue_id)
    _check_dates(event, body)
    return await crud.event.update(db, event, body)


@router.delete("/{event_id}", status_code=204)
async def delete_event(event_id: int, db: SessionDep, admin: CurrentAdmin):
    event = or_404(await crud.event.get(db, event_id), "Event")
    await remove_or_409(
        db,
        crud.event,
        event,
        "Event has reservations and can't be deleted; set its status to 'cancelled' instead",
    )
