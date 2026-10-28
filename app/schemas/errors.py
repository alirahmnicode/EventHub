from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    type: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
