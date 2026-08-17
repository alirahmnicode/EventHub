from .event import router as event_router
from .ticket_types import router as ticket_router
from .venue import router as venue_router

routers = [
    event_router,
    ticket_router,
    venue_router,
]
