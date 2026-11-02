from collections.abc import Sequence
from datetime import datetime

from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models.enums import EventStatus, UserRole
from app.models.event import Event
from app.models.ticket_type import TicketType
from app.models.user import User
from app.repositories.event import EventRepository
from app.repositories.ticket_type import TicketTypeRepository
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate

MAX_PAGE_SIZE = 100


class TicketTypeService:
    def __init__(self, repo: TicketTypeRepository, event_repo: EventRepository):
        self.repo = repo
        self.event_repo = event_repo

    # ---------- helpers ----------

    @staticmethod
    def _is_admin(user: User | None) -> bool:
        return user is not None and user.role == UserRole.ADMIN

    @staticmethod
    def _is_valid_sales_window(
        starts_at: datetime | None, ends_at: datetime | None
    ) -> bool:
        if starts_at is None or ends_at is None:
            return True  # an open-ended window is allowed
        return starts_at < ends_at

    async def _get_event_or_404(self, event_id: int) -> Event:
        event = await self.event_repo.get(event_id)
        if event is None:
            raise NotFoundError(message="Event not found")
        return event

    def _ensure_event_visible(self, event: Event, user: User | None) -> None:
        if event.status == EventStatus.DRAFT and not self._is_admin(user):
            raise PermissionDeniedError(
                message="Current user does not have access to this object."
            )

    async def _get_or_404(self, ticket_type_id: int) -> TicketType:
        ticket_type = await self.repo.get(ticket_type_id)
        if ticket_type is None:
            raise NotFoundError(message="Ticket type not found")
        return ticket_type

    async def _get_modifiable(self, ticket_type_id: int, user: User) -> TicketType:
        ticket_type = await self._get_or_404(ticket_type_id)
        if not self._is_admin(user):
            raise PermissionDeniedError()
        return ticket_type

    # ---------- use cases ----------

    async def get_ticket_type(
        self, ticket_type_id: int, user: User | None = None
    ) -> TicketType:
        ticket_type = await self._get_or_404(ticket_type_id)
        event = await self._get_event_or_404(ticket_type.event_id)
        self._ensure_event_visible(event, user)
        return ticket_type

    async def list_ticket_types(
        self,
        event_id: int,
        *,
        user: User | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[TicketType]:
        event = await self._get_event_or_404(event_id)
        self._ensure_event_visible(event, user)

        return await self.repo.get_list(
            filters=[TicketType.event_id == event_id],
            order_by=[TicketType.price_cents.asc(), TicketType.id.asc()],
            offset=max(offset, 0),
            limit=min(max(limit, 1), MAX_PAGE_SIZE),
        )

    async def create_ticket_type(
        self, data: TicketTypeCreate, user: User
    ) -> TicketType:
        if not self._is_admin(user):
            raise PermissionDeniedError()

        await self._get_event_or_404(data.event_id)

        if not self._is_valid_sales_window(data.sales_start_at, data.sales_end_at):
            raise DomainValidationError(
                message="The sales end date must be after the sales start date."
            )
        return await self.repo.create(data)

    async def update_ticket_type(
        self, ticket_type_id: int, data: TicketTypeUpdate, user: User
    ) -> TicketType:
        ticket_type = await self._get_modifiable(ticket_type_id, user)

        # Sales window: merge sent values with stored ones.
        # A date that is sent (even as null) replaces the stored value.
        sent = data.model_fields_set
        if sent & {"sales_start_at", "sales_end_at"}:
            starts_at = (
                data.sales_start_at
                if "sales_start_at" in sent
                else ticket_type.sales_start_at
            )
            ends_at = (
                data.sales_end_at
                if "sales_end_at" in sent
                else ticket_type.sales_end_at
            )
            if not self._is_valid_sales_window(starts_at, ends_at):
                raise DomainValidationError(
                    message="The sales end date must be after the sales start date."
                )

        # Inventory: can't shrink below what is already reserved or sold.
        if data.total_quantity is not None:
            committed = ticket_type.reserved_quantity + ticket_type.sold_quantity
            if data.total_quantity < committed:
                raise ConflictError(
                    message=(
                        f"Total quantity cannot be lower than the {committed} "
                        "tickets already reserved or sold."
                    ),
                    code="quantity_below_committed",
                )

        return await self.repo.update(ticket_type, data)

    async def delete_ticket_type(self, ticket_type_id: int, user: User) -> None:
        ticket_type = await self._get_modifiable(ticket_type_id, user)

        if ticket_type.reserved_quantity > 0 or ticket_type.sold_quantity > 0:
            raise ConflictError(
                message="Cannot delete a ticket type that has reserved or sold tickets.",
                code="ticket_type_in_use",
            )
        await self.repo.delete(ticket_type)
