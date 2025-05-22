from fastapi import APIRouter
from .assistant import router as assistant_router
from .user import router as user_router
from .settings import router as settings_router
from .documents import router as documents_router

api_router = APIRouter()

api_router.include_router(assistant_router, prefix="/assistant", tags=["assistant"])
api_router.include_router(user_router, prefix="/user", tags=["user"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])