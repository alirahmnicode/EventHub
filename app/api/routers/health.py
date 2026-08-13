from fastapi import APIRouter
 
router = APIRouter(tags=["health"])
 
 
@router.get("/healthz", status_code=200)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
 