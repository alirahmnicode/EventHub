from fastapi import APIRouter

from app.api.routes import auth, events, ops, ticket_types, venues

api_router = APIRouter()
api_router.include_router(ops.router)
api_router.include_router(auth.router)
api_router.include_router(venues.router)
api_router.include_router(events.router)
api_router.include_router(ticket_types.router)
