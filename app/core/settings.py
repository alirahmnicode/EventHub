"""
Env var mapping uses per-group prefixes (single underscore), e.g.:
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_PASSWORD=supersecret   <-- required, no default
  REDIS_URL=redis://localhost:6379/0
  JWT__SECRET_KEY=...              <-- required, no default (nested under top-level Settings, if applicable)
  APP_ENV=production
  APP_DEBUG=false
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).parent.parent.parent / ".env"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_", env_file=ENV_PATH, extra="ignore"
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    db: str = "app"

    password: SecretStr

    pool_size: int = 5
    echo: bool = False

    @property
    def dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: RedisDsn = Field(default="redis://localhost:6379/0")

    password: SecretStr | None = None


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = "my-fastapi-app"
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class Settings(BaseSettings):
    """
    Top-level settings, aggregating nested config groups.

    Loads from a `.env` file (if present) and the process environment.
    Environment variables always take precedence over `.env` file values.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)

    @property
    def database_url(self) -> str:
        if self.app.env == "development":
            return "sqlite+aiosqlite:///./test.db"
        return self.database.dsn


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor for use as a FastAPI dependency.

    Usage:
        from fastapi import Depends

        @app.get("/health")
        def health(settings: Settings = Depends(get_settings)):
            return {"env": settings.app.env}
    """
    return Settings()


settings = get_settings()
