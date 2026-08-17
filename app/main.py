from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, health
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def _configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routers(app: FastAPI) -> None:
    # admin routers
    for router in admin.routers:
        app.include_router(router)

    app.include_router(health.router)
    app.include_router(auth.router)


def _lifespan_factory(settings: Settings):
    """
    Returns a lifespan context manager closed over `settings`, so
    startup/shutdown can open/close resources (DB pool, redis pool)
    using the settings this app instance was built with.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # --- startup ---
        # app.state.db_pool = await create_db_pool(settings.database.dsn)
        # app.state.redis = await create_redis_pool(settings.redis.url)
        yield
        # --- shutdown ---
        # await app.state.db_pool.close()
        # await app.state.redis.close()

    return lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.app.name,
        debug=settings.app.debug,
        lifespan=_lifespan_factory(settings),
    )

    app.state.settings = settings

    _configure_cors(app, settings)
    _register_routers(app)

    # add custom exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    return app


app = create_app()
