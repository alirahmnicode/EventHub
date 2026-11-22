from fastapi import APIRouter, status

from app import crud
from app.api.deps import (
    CurrentAdmin,
    EventServiceDep,
    SessionDep,
    TicketTypeServiceDep,
    VenueServiceDep,
)
from app.schemas import (
    EventCreate,
    EventRead,
    EventUpdate,
    TicketTypeCreate,
    TicketTypeRead,
    TicketTypeUpdate,
    VenueCreate,
    VenueRead,
    VenueUpdate,
)
from app.utils import or_404

router = APIRouter(prefix="/admin", tags=["admin"])


async def _require_venue(db: SessionDep, venue_id: int) -> None:
    or_404(await crud.venue.get(db, venue_id), "Venue")


@router.post("/events", response_model=EventRead, status_code=201)
async def create_event(body: EventCreate, db: SessionDep, admin: CurrentAdmin):
    await _require_venue(db, body.venue_id)
    # status defaults to "draft"; publish with PATCH once ticket types exist
    return await crud.event.create(db, body, created_by=admin.id)


@router.patch("/events/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int, body: EventUpdate, service: EventServiceDep, admin: CurrentAdmin
):
    return await service.update_event(event_id=event_id, data=body, user=admin)


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: int, service: EventServiceDep, admin: CurrentAdmin):
    return await service.delete_event(event_id=event_id, user=admin)


@router.post(
    "/ticket-types", response_model=TicketTypeRead, status_code=status.HTTP_201_CREATED
)
async def create_ticket_type(
    data: TicketTypeCreate, service: TicketTypeServiceDep, user: CurrentAdmin
):
    return await service.create_ticket_type(data, user)


@router.patch("/ticket-types/{ticket_type_id}", response_model=TicketTypeRead)
async def update_ticket_type(
    ticket_type_id: int,
    data: TicketTypeUpdate,
    service: TicketTypeServiceDep,
    user: CurrentAdmin,
):
    return await service.update_ticket_type(ticket_type_id, data, user)


@router.delete("/ticket-types/{ticket_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_type(
    ticket_type_id: int, service: TicketTypeServiceDep, user: CurrentAdmin
):
    await service.delete_ticket_type(ticket_type_id, user)


@router.post("/venues", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
async def create_venue(data: VenueCreate, service: VenueServiceDep, user: CurrentAdmin):
    return await service.create_venue(data, user)


@router.patch("/venues/{venue_id}", response_model=VenueRead)
async def update_venue(
    venue_id: int, data: VenueUpdate, service: VenueServiceDep, user: CurrentAdmin
):
    return await service.update_venue(venue_id, data, user)


@router.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(venue_id: int, service: VenueServiceDep, user: CurrentAdmin):
    await service.delete_venue(venue_id, user)
