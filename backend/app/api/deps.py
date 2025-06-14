"""
API Dependencies for JarvisAI
Common dependencies used across API endpoints
"""

from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.security import validate_token, extract_token_from_bearer
from app.models.user import User, UserRole

logger = structlog.get_logger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False  # Don't auto raise 401, we'll handle it
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token
    Returns None if no valid token is provided
    """
    if not token:
        return None
    
    # Validate token
    payload = validate_token(token, token_type="access")
    if not payload:
        return None
    
    # Get user from database
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        logger.warning("Invalid user ID in token", user_id=user_id)
        return None
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalars().first()
    
    if not user:
        logger.warning("User not found", user_id=user_id)
        return None
    
    return user


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Get current active user
    Raises 401 if no valid user or user is inactive
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user
    Raises 403 if user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User email not verified"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user
    Raises 403 if user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


class RateLimiter:
    """
    Simple rate limiter dependency
    In production, use Redis for distributed rate limiting
    """
    def __init__(self, requests: int = 10, window: int = 60):
        self.requests = requests
        self.window = window
        # In-memory store for demo - use Redis in production
        self.requests_store = {}
    
    async def __call__(self, current_user: Optional[User] = Depends(get_current_user)):
        # Simple implementation - in production use Redis
        # This is just a placeholder
        return True


# Common rate limiters
rate_limit_low = RateLimiter(requests=10, window=60)  # 10 requests per minute
rate_limit_medium = RateLimiter(requests=60, window=60)  # 60 requests per minute
rate_limit_high = RateLimiter(requests=300, window=60)  # 300 requests per minute


class PaginationParams:
    """Common pagination parameters"""
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        max_limit: int = 100
    ):
        self.skip = skip
        self.limit = min(limit, max_limit)


async def get_api_key_user(
    api_key: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get user from API key (for service-to-service auth)
    """
    # Implementation for API key authentication
    # This is a placeholder - implement based on your needs
    return None