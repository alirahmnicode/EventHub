from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentAdmin, Limit, Offset, SessionDep
from app.models.enums import EventStatus
from app.schemas import TicketTypeCreate, TicketTypeRead, TicketTypeUpdate
from app.utils import or_404, remove_or_409

router = APIRouter(prefix="/ticket-types", tags=["ticket types"])


@router.post("", response_model=TicketTypeRead, status_code=201)
async def create_ticket_type(
    body: TicketTypeCreate, db: SessionDep, admin: CurrentAdmin
):
    event = or_404(await crud.event.get(db, body.event_id), "Event")
    if event.status == EventStatus.CANCELLED:
        raise HTTPException(409, "Can't add ticket types to a cancelled event")
    return await crud.ticket_type.create(db, body)


@router.get("", response_model=list[TicketTypeRead])
async def list_ticket_types(
    db: SessionDep, event_id: int | None = None, offset: Offset = 0, limit: Limit = 20
):
    return await crud.ticket_type.search(
        db, event_id=event_id, offset=offset, limit=limit
    )


@router.get("/{ticket_type_id}", response_model=TicketTypeRead)
async def get_ticket_type(ticket_type_id: int, db: SessionDep):
    return or_404(await crud.ticket_type.get(db, ticket_type_id), "Ticket type")


@router.patch("/{ticket_type_id}", response_model=TicketTypeRead)
async def update_ticket_type(
    ticket_type_id: int, body: TicketTypeUpdate, db: SessionDep, admin: CurrentAdmin
):
    # Row lock: reservations can't change reserved/sold while we validate and save.
    tt = or_404(
        await crud.ticket_type.get_for_update(db, ticket_type_id), "Ticket type"
    )

    # Explicit null in the body clears the field; an absent field keeps the stored value.
    fields = body.model_fields_set
    start = body.sales_start_at if "sales_start_at" in fields else tt.sales_start_at
    end = body.sales_end_at if "sales_end_at" in fields else tt.sales_end_at
    if start and end and end <= start:
        raise HTTPException(422, "sales_end_at must be after sales_start_at")

    committed = tt.reserved_quantity + tt.sold_quantity
    if body.total_quantity is not None and body.total_quantity < committed:
        raise HTTPException(
            409, f"total_quantity can't be lower than reserved + sold ({committed})"
        )
    return await crud.ticket_type.update(db, tt, body)


@router.delete("/{ticket_type_id}", status_code=204)
async def delete_ticket_type(ticket_type_id: int, db: SessionDep, admin: CurrentAdmin):
    tt = or_404(await crud.ticket_type.get(db, ticket_type_id), "Ticket type")
    await remove_or_409(
        db, crud.ticket_type, tt, "Ticket type has reservations and can't be deleted"
    )
