from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.models.ticket_type import TicketType


class ReservationRepository:
    """The only place that touches the DB session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- reads -------------------------------------------------------------

    async def get(
        self, reservation_id: int, *, for_update: bool = False
    ) -> Reservation | None:
        stmt = select(Reservation).where(Reservation.id == reservation_id)
        if for_update:
            stmt = stmt.with_for_update()
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_idempotency_key(
        self, user_id: int, idempotency_key: str
    ) -> Reservation | None:
        stmt = select(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.idempotency_key == idempotency_key,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        *,
        status: ReservationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Reservation]:
        stmt = select(Reservation).where(Reservation.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Reservation.status == status)
        stmt = (
            stmt.order_by(Reservation.created_at.desc(), Reservation.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.execute(stmt)).scalars().all()

    async def get_available_quantity_locked(
        self, ticket_type_id: int, now: datetime
    ) -> int | None:
        """Lock the ticket type row and return how many tickets are still free.

        Returns None if the ticket type doesn't exist. The lock serializes
        concurrent reservations for the same ticket type until commit.
        """
        stmt = (
            select(TicketType).where(TicketType.id == ticket_type_id).with_for_update()
        )
        ticket_type = (await self._session.execute(stmt)).scalar_one_or_none()
        if ticket_type is None:
            return None

        held = await self._sum_active_quantity(ticket_type_id, now)
        return ticket_type.total_quantity - held  # adjust field name

    async def _sum_active_quantity(self, ticket_type_id: int, now: datetime) -> int:
        """Confirmed + pending-and-not-yet-expired."""
        stmt = select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
            Reservation.ticket_type_id == ticket_type_id,
            or_(
                Reservation.status == ReservationStatus.CONFIRMED,
                and_(
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.expires_at > now,
                ),
            ),
        )
        return int((await self._session.execute(stmt)).scalar_one())

    # ---- writes ------------------------------------------------------------

    async def create_or_get(self, reservation: Reservation) -> tuple[Reservation, bool]:
        """Insert the reservation, or return the existing one for the same
        (user_id, idempotency_key) if a concurrent request beat us to it.

        Returns (reservation, created).
        """
        try:
            # Savepoint, so a unique violation doesn't poison the outer tx.
            async with self._session.begin_nested():
                self._session.add(reservation)
                await self._session.flush()
        except IntegrityError:
            existing = await self.get_by_idempotency_key(
                reservation.user_id, reservation.idempotency_key
            )
            if existing is None:
                raise  # a different constraint failed
            return existing, False

        # Load server defaults (created_at, status) to avoid lazy IO later.
        await self._session.refresh(reservation)
        return reservation, True

    async def expire_stale(self, now: datetime) -> int:
        """Bulk-flip overdue PENDING reservations to EXPIRED."""
        stmt = (
            update(Reservation)
            .where(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.expires_at <= now,
            )
            .values(status=ReservationStatus.EXPIRED)
            .returning(Reservation.id)
        )
        result = await self._session.execute(stmt)
        return len(result.all())

    async def commit(self) -> None:
        await self._session.commit()
