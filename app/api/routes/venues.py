from fastapi import APIRouter, status

from app.api.deps import CurrentAdmin, Limit, Offset, VenueServiceDep
from app.schemas import VenueCreate, VenueRead, VenueUpdate

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("", response_model=list[VenueRead])
async def list_venues(
    service: VenueServiceDep,
    search: str | None = None,
    city: str | None = None,
    skip: Limit = 0,
    limit: Offset = 20,
):
    return await service.list_venues(search=search, city=city, skip=skip, limit=limit)


@router.get("/{venue_id}", response_model=VenueRead)
async def get_venue(venue_id: int, service: VenueServiceDep):
    return await service.get_venue(venue_id)
