"""
JarvisAI FastAPI Backend
Main application entry point for the JarvisAI API Gateway
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.middleware.auth import AuthMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.api.v1.router import api_router
from app.core.exceptions import JarvisException


# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting JarvisAI API Gateway", version=settings.VERSION)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize AI services connections
    # This will be expanded as we add Ollama, Qdrant, etc.
    logger.info("AI services connections initialized")
    
    yield
    
    logger.info("Shutting down JarvisAI API Gateway")


# Create FastAPI application
app = FastAPI(
    title="JarvisAI API Gateway",
    description="Self-hosted AI assistant with multi-model support and RAG capabilities",
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Authentication middleware
app.add_middleware(AuthMiddleware)

# Global exception handler
@app.exception_handler(JarvisException)
async def jarvis_exception_handler(request: Request, exc: JarvisException):
    """Handle custom JarvisAI exceptions"""
    logger.error(
        "JarvisAI exception occurred",
        error_code=exc.error_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "timestamp": exc.timestamp.isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "Unexpected exception occurred",
        exception=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "jarvis-api-gateway",
        "version": settings.VERSION,
        "debug": settings.DEBUG
    }

# Readiness check endpoint
@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for container orchestration"""
    # TODO: Add actual service dependency checks
    return {
        "status": "ready",
        "services": {
            "database": "connected",
            "redis": "connected",
            "ollama": "checking",
            "qdrant": "checking"
        }
    }

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "service": "JarvisAI API Gateway",
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
        "metrics": "/metrics"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use our custom logging
        access_log=False   # Use our middleware for access logging
    )