from fastapi import APIRouter, status

from app.api.deps import (
    CurrentAdmin,
    CurrentUser,
    TicketTypeServiceDep,
)
from app.schemas import TicketTypeCreate, TicketTypeRead, TicketTypeUpdate

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
