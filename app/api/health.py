import logging

from fastapi import APIRouter

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)


@router.get("/healthz", status_code=200)
async def healthz() -> dict[str, str]:
    logger.info("handling health check")
    return {"status": "ok"}
