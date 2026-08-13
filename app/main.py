from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import health
from app.core.settings import Settings, get_settings


def _configure_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routers(app: FastAPI) -> None:
    app.include_router(health.router)


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

    return app


app = create_app()
