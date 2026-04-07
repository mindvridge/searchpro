from fastapi import APIRouter

from app.api.v1.endpoints import admin, programs

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(programs.router)


@api_router.get("/ping")
async def ping():
    return {"message": "pong"}
