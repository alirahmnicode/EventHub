from fastapi import APIRouter

from app.api.deps import (
    CurrentUser,
    TicketTypeServiceDep,
)
from app.schemas import TicketTypeRead

router = APIRouter(prefix="/ticket-types", tags=["ticket types"])


@router.get("/events/{event_id}/ticket-types", response_model=list[TicketTypeRead])
async def list_ticket_types(
    event_id: int,
    service: TicketTypeServiceDep,
    user: CurrentUser,
    offset: int = 0,
    limit: int = 20,
):
    return await service.list_ticket_types(
        event_id, user=user, offset=offset, limit=limit
    )


@router.get("/ticket-types/{ticket_type_id}", response_model=TicketTypeRead)
async def get_ticket_type(
    ticket_type_id: int, service: TicketTypeServiceDep, user: CurrentUser
):
    return await service.get_ticket_type(ticket_type_id, user)
