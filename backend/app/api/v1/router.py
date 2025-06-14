"""
JarvisAI API Router
Main API router that includes all endpoint modules
"""

from fastapi import APIRouter

# Import endpoint routers (will be created)
# from app.api.v1.endpoints import auth, chat, models, documents, agents

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(models.router, prefix="/models", tags=["models"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

# Placeholder health endpoint for API v1
@api_router.get("/health")
async def api_health():
    """API v1 health check"""
    return {"status": "healthy", "version": "v1"}