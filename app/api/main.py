from fastapi import APIRouter

from app.api.routes import auth, ops

api_router = APIRouter()
api_router.include_router(ops.router)
api_router.include_router(auth.router)
