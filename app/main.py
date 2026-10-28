import re
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.main import api_router
from app.core.exceptions import ERROR_RESPONSES
from app.core.handlers import register_error_handlers
from app.core.settings import settings

app = FastAPI(responses=ERROR_RESPONSES)

register_error_handlers(app)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Response-Time"] = str(process_time)
    return response


app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(request: Request, call_next) -> Response:
    _VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
    incomming = request.headers.get("x-request-id", None)
    rid = incomming if incomming and _VALID_ID.match(incomming) else uuid.uuid4().hex
    request.state.request_id = rid

    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)
