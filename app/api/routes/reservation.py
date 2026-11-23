from fastapi import APIRouter, Header, HTTPException, status

from app.api.deps import CurrentUser, ReservationServiceDep
from app.schemas import ReservationCreate, ReservationRead
from app.services.exceptions import *

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create(
    data: ReservationCreate,
    service: ReservationServiceDep,
    user: CurrentUser,
    idempotency_key: str = Header(..., alias="Idempotency-Key", max_length=255),
):
    try:
        return await service.create(
            user_id=user.id,
            ticket_type_id=data.ticket_type_id,
            quantity=data.quantity,
            idempotency_key=idempotency_key,
        )
    except TicketTypeNotFoundError:
        raise HTTPException(404, "Ticket type not found")
    except InsufficientInventoryError as e:
        raise HTTPException(409, f"Only {e.available} ticket(s) available")
    except IdempotencyConflictError:
        raise HTTPException(422, "Idempotency key reused with different parameters")


@router.post(
    "/{reservation_id}/cancel",
    response_model=ReservationRead,
    status_code=status.HTTP_200_OK,
)
async def cancel_reservation(
    reservation_id: int,
    user: CurrentUser,
    service: ReservationServiceDep,
):
    try:
        return await service.cancel(reservation_id, user_id=user.id)
    except ReservationNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reservation not found")
    except InvalidReservationStateError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
