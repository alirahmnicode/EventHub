from app.schemas.errors import ErrorDetail, ErrorResponse

ERROR_RESPONSES: dict[int | str, dict] = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    message = "Internal server error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: list[ErrorDetail] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        self.headers = headers
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code, code, message = 400, "bad_request", "Bad request"


class UnauthorizedError(AppError):
    status_code, code, message = 401, "unauthorized", "Authentication required"


class ForbiddenError(AppError):
    status_code, code, message = 403, "forbidden", "You do not have access"


class NotFoundError(AppError):
    status_code, code, message = 404, "not_found", "Resource not found"


class ConflictError(AppError):
    status_code, code, message = 409, "conflict", "Resource conflict"
