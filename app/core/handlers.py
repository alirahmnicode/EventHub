import logging
import re
import uuid
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger("app.errors")


def _request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if not rid:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = rid
    return rid


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    rid = _request_id(request)
    body = ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details, request_id=rid)
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers={**(headers or {}), "X-Request-ID": rid},
    )


def _code_for_status(status_code: int) -> str:
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        return "error"
    return re.sub(r"[^a-z0-9]+", "_", phrase.lower()).strip("_")


# ---------- Handlers ----------


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        request, exc.status_code, exc.code, exc.message, exc.details, exc.headers
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # Catches FastAPI's HTTPException too, plus Starlette's own 404/405.
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _error_response(
        request,
        exc.status_code,
        _code_for_status(exc.status_code),
        message,
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = [
        ErrorDetail(
            field=".".join(str(p) for p in err["loc"]),
            message=err["msg"],
            type=err["type"],
        )
        for err in exc.errors()
    ]
    return _error_response(
        request, 422, "validation_error", "Request validation failed", details
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Never leak internals to the client; log the real error with the request id.
    logger.exception("Unhandled error [request_id=%s]", _request_id(request))
    return _error_response(
        request, 500, "internal_error", "An unexpected error occurred"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
