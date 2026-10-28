from fastapi import APIRouter

from app import crud
from app.api.deps import CurrentAdmin, Limit, Offset, SessionDep
from app.schemas import VenueCreate, VenueRead, VenueUpdate
from app.utils import or_404, remove_or_409

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("", response_model=VenueRead, status_code=201)
async def create_venue(body: VenueCreate, db: SessionDep, admin: CurrentAdmin):
    return await crud.venue.create(db, body, created_by=admin.id)


@router.get("", response_model=list[VenueRead])
async def list_venues(
    db: SessionDep, city: str | None = None, offset: Offset = 0, limit: Limit = 20
):
    return await crud.venue.search(db, city=city, offset=offset, limit=limit)


@router.get("/{venue_id}", response_model=VenueRead)
async def get_venue(venue_id: int, db: SessionDep):
    return or_404(await crud.venue.get(db, venue_id), "Venue")


@router.patch("/{venue_id}", response_model=VenueRead)
async def update_venue(
    venue_id: int, body: VenueUpdate, db: SessionDep, admin: CurrentAdmin
):
    venue = or_404(await crud.venue.get(db, venue_id), "Venue")
    return await crud.venue.update(db, venue, body)


@router.delete("/{venue_id}", status_code=204)
async def delete_venue(venue_id: int, db: SessionDep, admin: CurrentAdmin):
    venue = or_404(await crud.venue.get(db, venue_id), "Venue")
    await remove_or_409(
        db, crud.venue, venue, "Venue still has events; delete or move them first"
    )
