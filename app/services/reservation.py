from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone

from app.models.enums import ReservationStatus
from app.models.reservation import Reservation
from app.repositories.reservation import ReservationRepository
from app.services.exceptions import (
    IdempotencyConflictError,
    InsufficientInventoryError,
    InvalidQuantityError,
    InvalidReservationStateError,
    ReservationExpiredError,
    ReservationNotFoundError,
    TicketTypeNotFoundError,
)

DEFAULT_HOLD = timedelta(minutes=15)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReservationService:
    def __init__(
        self,
        repo: ReservationRepository,
        hold_duration: timedelta = DEFAULT_HOLD,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._repo = repo
        self._hold_duration = hold_duration
        self._clock = clock

    # ---- create ------------------------------------------------------------

    async def create(
        self,
        *,
        user_id: int,
        ticket_type_id: int,
        quantity: int,
        idempotency_key: str,
    ) -> Reservation:
        if quantity <= 0:
            raise InvalidQuantityError("quantity must be positive")

        # Fast path: client retry of a request we've already handled.
        existing = await self._repo.get_by_idempotency_key(user_id, idempotency_key)
        if existing:
            return self._replay(existing, ticket_type_id, quantity)

        now = self._clock()

        # Locks the ticket type, so concurrent reservations can't oversell.
        available = await self._repo.get_available_quantity_locked(ticket_type_id, now)
        if available is None:
            raise TicketTypeNotFoundError(f"Ticket type {ticket_type_id}")

        # Re-check under the lock: a same-key retry may have committed
        # while we were waiting for it.
        existing = await self._repo.get_by_idempotency_key(user_id, idempotency_key)
        if existing:
            return self._replay(existing, ticket_type_id, quantity)

        if quantity > available:
            raise InsufficientInventoryError(max(available, 0))

        reservation, created = await self._repo.create_or_get(
            Reservation(
                user_id=user_id,
                ticket_type_id=ticket_type_id,
                quantity=quantity,
                idempotency_key=idempotency_key,
                expires_at=now + self._hold_duration,
            )
        )
        if not created:
            return self._replay(reservation, ticket_type_id, quantity)

        await self._repo.commit()
        return reservation

    @staticmethod
    def _replay(
        existing: Reservation, ticket_type_id: int, quantity: int
    ) -> Reservation:
        if existing.ticket_type_id != ticket_type_id or existing.quantity != quantity:
            raise IdempotencyConflictError(
                "Idempotency key was already used with different parameters"
            )
        return existing

    # ---- read --------------------------------------------------------------

    async def get(self, reservation_id: int, *, user_id: int) -> Reservation:
        return await self._get_owned(reservation_id, user_id)

    async def list_for_user(
        self,
        user_id: int,
        *,
        status: ReservationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Reservation]:
        return await self._repo.list_for_user(
            user_id, status=status, limit=limit, offset=offset
        )

    # ---- state transitions -------------------------------------------------

    async def confirm(self, reservation_id: int, *, user_id: int) -> Reservation:
        reservation = await self._get_owned(reservation_id, user_id, for_update=True)

        if reservation.status == ReservationStatus.CONFIRMED:
            return reservation  # idempotent
        if reservation.status != ReservationStatus.PENDING:
            raise InvalidReservationStateError(reservation.status.value, "confirm")

        if reservation.expires_at <= self._clock():
            reservation.status = ReservationStatus.EXPIRED
            await self._repo.commit()
            raise ReservationExpiredError(f"Reservation {reservation_id}")

        reservation.status = ReservationStatus.CONFIRMED
        await self._repo.commit()
        return reservation

    async def cancel(self, reservation_id: int, *, user_id: int) -> Reservation:
        reservation = await self._get_owned(reservation_id, user_id, for_update=True)

        if reservation.status == ReservationStatus.CANCELLED:
            return reservation
        if reservation.status not in (
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
        ):
            raise InvalidReservationStateError(reservation.status.value, "cancel")

        reservation.status = ReservationStatus.CANCELLED
        await self._repo.commit()
        return reservation

    # ---- background job ----------------------------------------------------

    async def expire_stale_reservations(self) -> int:
        count = await self._repo.expire_stale(self._clock())
        await self._repo.commit()
        return count

    # ---- helpers -----------------------------------------------------------

    async def _get_owned(
        self, reservation_id: int, user_id: int, *, for_update: bool = False
    ) -> Reservation:
        reservation = await self._repo.get(reservation_id, for_update=for_update)
        # Same error for "missing" and "not yours" so IDs can't be probed.
        if reservation is None or reservation.user_id != user_id:
            raise ReservationNotFoundError(f"Reservation {reservation_id}")
        return reservation
