from fastapi import APIRouter

from app.api.v1.endpoints import admin, alerts, auth, bookmarks, programs, recommendations

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(alerts.router)
api_router.include_router(auth.router)
api_router.include_router(bookmarks.router)
api_router.include_router(programs.router)
api_router.include_router(recommendations.router)


@api_router.get("/ping")
async def ping():
    return {"message": "pong"}
