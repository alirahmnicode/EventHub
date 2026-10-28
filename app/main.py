from fastapi import FastAPI

from app.api.main import api_router
from app.core.exceptions import ERROR_RESPONSES
from app.core.handlers import register_error_handlers
from app.core.settings import settings

app = FastAPI(responses=ERROR_RESPONSES)

register_error_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_STR)
