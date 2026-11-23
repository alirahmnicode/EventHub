class ReservationError(Exception):
    """Base class for reservation domain errors."""


class ReservationNotFoundError(ReservationError):
    pass


class TicketTypeNotFoundError(ReservationError):
    pass


class InvalidQuantityError(ReservationError):
    pass


class InsufficientInventoryError(ReservationError):
    def __init__(self, available: int) -> None:
        super().__init__(f"Only {available} ticket(s) available")
        self.available = available


class IdempotencyConflictError(ReservationError):
    """Same idempotency key reused with a different payload."""


class ReservationExpiredError(ReservationError):
    pass


class InvalidReservationStateError(ReservationError):
    def __init__(self, current: str, action: str) -> None:
        super().__init__(f"Cannot {action} a reservation that is {current}")
        self.current = current
        self.action = action
