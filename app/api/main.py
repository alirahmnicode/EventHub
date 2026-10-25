from fastapi import APIRouter

from app.api.routes import ops

api_router = APIRouter()
api_router.include_router(ops.router)
