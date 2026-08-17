from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.paginator import PaginatedResponse, paginate
from app.db.engine import get_db
from app.models import User, Venue
from app.schemas.venue import VenueCreateSchema, VenueReadSchema, VenueUpdateSchema

router = APIRouter(prefix="/admin/venue", tags=["Admin Venue"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=VenueReadSchema)
async def create_venue(
    venue: VenueCreateSchema,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    venue_obj = Venue(**venue.model_dump())
    venue_obj.created_by = admin.id

    db.add(venue_obj)

    await db.commit()
    await db.refresh(venue_obj)

    return venue_obj


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedResponse[VenueReadSchema],
)
async def get_venues(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Venue)

    return await paginate(
        entity=Venue,
        query=query,
        schema=VenueReadSchema,
        db=db,
        request=request,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{venue_id}", status_code=status.HTTP_200_OK, response_model=VenueReadSchema
)
async def get_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Venue).where(Venue.id == venue_id))

    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    return venue


@router.patch(
    "/{venue_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=VenueReadSchema,
)
async def update_venue(
    venue_id: int,
    payload: VenueUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    # Only update fields that were actually provided
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(venue, field, value)

    await db.commit()
    await db.refresh(venue)

    return venue


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_venue(
    venue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):

    result = await db.execute(select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )

    await db.delete(venue)
    await db.commit()

    return {
        "message": "Venue deleted successfully",
    }
