"""
JarvisAI Authentication Middleware
JWT-based authentication with OAuth2 support
"""

from typing import Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.security import validate_token, extract_token_from_bearer
from app.core.config import settings

logger = structlog.get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for request processing"""
    
    def __init__(self, app):
        super().__init__(app)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health", 
            "/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/oauth",
            "/api/v1/auth/callback",
            "/api/v1/health"
        }
        
        # Paths that start with these prefixes are public
        self.public_path_prefixes = [
            "/api/v1/auth/oauth/",
            "/api/v1/auth/callback/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request authentication"""
        
        # Check if path is public
        path = request.url.path
        is_public = (
            path in self.public_paths or
            any(path.startswith(prefix) for prefix in self.public_path_prefixes)
        )
        
        # Skip authentication for public paths
        if is_public:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # In development mode, log warning but allow request
            if settings.DEBUG:
                logger.warning(
                    "Request without authorization header in DEBUG mode", 
                    path=path
                )
                return await call_next(request)
            
            # In production, return 401
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "unauthorized",
                    "detail": "Missing authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract and validate token
        token = extract_token_from_bearer(auth_header)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_header",
                    "detail": "Invalid authorization header format"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        payload = validate_token(token, token_type="access")
        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "invalid_token",
                    "detail": "Invalid or expired token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Store user info in request state for later use
        request.state.user_id = payload.get("sub")
        request.state.user_email = payload.get("email")
        request.state.user_role = payload.get("role")
        
        # Log authenticated request
        logger.debug(
            "Authenticated request",
            path=path,
            user_id=request.state.user_id,
            method=request.method
        )
        
        response = await call_next(request)
        return response