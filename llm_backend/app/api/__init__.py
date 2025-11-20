from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.assist import router as assist_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(assist_router, tags=["assist"])