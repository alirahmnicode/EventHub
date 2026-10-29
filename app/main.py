from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.main import api_router
from app.core.exceptions import ERROR_RESPONSES
from app.core.handlers import register_error_handlers
from app.core.middlewares import RateLimitMiddleware, RequestContextMiddleware
from app.core.settings import settings

app = FastAPI(responses=ERROR_RESPONSES)

register_error_handlers(app)

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
    expose_headers=settings.EXPOSE_HEADERS,
)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router, prefix=settings.API_V1_STR)
