from fastapi import status
from fastapi.routing import APIRouter

router = APIRouter(prefix="/ops")


@router.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"message": "ok"}
