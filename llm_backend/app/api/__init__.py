from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.assist import router as assist_router
from app.api.conversation import router as conversation_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(assist_router, tags=["assist"])
api_router.include_router(conversation_router, tags=["conversation"])