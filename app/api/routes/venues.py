from fastapi import APIRouter, status

from app.api.deps import CurrentAdmin, Limit, Offset, VenueServiceDep
from app.schemas import VenueCreate, VenueRead, VenueUpdate

router = APIRouter(prefix="/venues", tags=["venues"])


router = APIRouter(
    prefix="/venues",
    tags=["venues"],
)


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


@router.post("", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
async def create_venue(data: VenueCreate, service: VenueServiceDep, user: CurrentAdmin):
    return await service.create_venue(data, user)


@router.patch("/{venue_id}", response_model=VenueRead)
async def update_venue(
    venue_id: int, data: VenueUpdate, service: VenueServiceDep, user: CurrentAdmin
):
    return await service.update_venue(venue_id, data, user)


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(venue_id: int, service: VenueServiceDep, user: CurrentAdmin):
    await service.delete_venue(venue_id, user)
