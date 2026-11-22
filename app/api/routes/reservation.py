from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.schemas import ReservationCreate

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/create", status_code=201)
async def reserve(data: ReservationCreate, db: SessionDep, user: CurrentUser):
    return {""}
