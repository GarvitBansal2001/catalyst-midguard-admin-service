from fastapi import APIRouter

router = APIRouter()

@router.get("/public/healthz")
async def health_check():
    return {"message": "OK"}