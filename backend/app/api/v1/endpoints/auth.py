"""
Authentication endpoints for JarvisAI
Login, logout, token refresh, and OAuth callbacks
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import structlog
import httpx

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    validate_token,
    get_password_hash
)
from app.core.config import settings
from app.models.user import (
    User, UserCreate, UserResponse, UserLogin, 
    TokenResponse, RefreshTokenRequest, UserOAuthCreate,
    OAuthProvider
)
from app.api.deps import get_current_user, get_current_active_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            or_(User.email == user_data.email, User.username == user_data.username)
        )
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        preferred_model=user_data.preferred_model,
        preferred_language=user_data.preferred_language,
        therapeutic_mode_enabled=user_data.therapeutic_mode_enabled,
        provider=OAuthProvider.LOCAL
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info("New user registered", user_id=str(user.id), username=user.username)
    
    return UserResponse.from_orm(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username/email and password
    OAuth2 compatible token endpoint
    """
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            or_(User.email == form_data.username, User.username == form_data.username)
        )
    )
    user = result.scalars().first()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info("User logged in", user_id=str(user.id), username=user.username)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Validate refresh token
    payload = validate_token(refresh_data.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == payload["sub"])
    )
    user = result.scalars().first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role.value
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info("Token refreshed", user_id=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user
    In a real implementation, we'd blacklist the token
    """
    # In production, you would:
    # 1. Add the current token to a blacklist in Redis
    # 2. Set token expiry in blacklist to match token expiry
    
    logger.info("User logged out", user_id=str(current_user.id))
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


# OAuth endpoints

@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """
    Initiate OAuth login flow
    """
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth not configured"
            )
        
        # Construct Google OAuth URL
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": f"{settings.API_URL}/api/v1/auth/callback/google",
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        
    elif provider == "github":
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="GitHub OAuth not configured"
            )
        
        # Construct GitHub OAuth URL
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": f"{settings.API_URL}/api/v1/auth/callback/github",
            "scope": "read:user user:email"
        }
        
        oauth_url = "https://github.com/login/oauth/authorize"
    
    # Build full URL with parameters
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    redirect_url = f"{oauth_url}?{param_string}"
    
    return {"redirect_url": redirect_url}


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback and create/login user
    """
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    try:
        # Exchange code for token
        if provider == "google":
            user_info = await _handle_google_callback(code)
        elif provider == "github":
            user_info = await _handle_github_callback(code)
        
        # Find or create user
        result = await db.execute(
            select(User).where(
                User.email == user_info["email"]
            )
        )
        user = result.scalars().first()
        
        if not user:
            # Create new user from OAuth
            user = User(
                email=user_info["email"],
                username=user_info.get("username", user_info["email"].split("@")[0]),
                full_name=user_info.get("name"),
                provider=OAuthProvider(provider),
                provider_id=user_info["id"],
                is_verified=True  # OAuth users are pre-verified
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(
                "New OAuth user registered", 
                user_id=str(user.id), 
                provider=provider
            )
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            await db.commit()
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Redirect to frontend with tokens
        frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
        redirect_url = (
            f"{frontend_url}/auth/callback"
            f"?access_token={access_token}"
            f"&refresh_token={refresh_token}"
        )
        
        return {"redirect_url": redirect_url}
        
    except Exception as e:
        logger.error("OAuth callback error", provider=provider, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authentication failed"
        )


async def _handle_google_callback(code: str) -> dict:
    """Handle Google OAuth callback"""
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{settings.API_URL}/api/v1/auth/callback/google",
                "grant_type": "authorization_code"
            }
        )
        token_data = token_response.json()
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_data = user_response.json()
        
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data.get("name"),
            "username": user_data["email"].split("@")[0]
        }


async def _handle_github_callback(code: str) -> dict:
    """Handle GitHub OAuth callback"""
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_response.json()
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_data = user_response.json()
        
        # Get primary email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        emails = email_response.json()
        primary_email = next(
            (e["email"] for e in emails if e["primary"]), 
            user_data.get("email")
        )
        
        return {
            "id": str(user_data["id"]),
            "email": primary_email,
            "name": user_data.get("name"),
            "username": user_data["login"]
        }