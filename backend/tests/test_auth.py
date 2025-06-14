"""
Test authentication endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.security import get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123",
                "full_name": "Test User"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


@pytest.mark.asyncio
async def test_login_user():
    """Test user login"""
    # First create a user (in real tests, use fixtures)
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "LoginPass123",
                "full_name": "Login User"
            }
        )
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "loginuser",
                "password": "LoginPass123"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user():
    """Test getting current user info"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "current@example.com",
                "username": "currentuser",
                "password": "CurrentPass123",
                "full_name": "Current User"
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "currentuser",
                "password": "CurrentPass123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["username"] == "currentuser"


@pytest.mark.asyncio
async def test_refresh_token():
    """Test token refresh"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "username": "refreshuser",
                "password": "RefreshPass123",
                "full_name": "Refresh User"
            }
        )
        
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "refreshuser",
                "password": "RefreshPass123"
            }
        )
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_invalid_login():
    """Test login with invalid credentials"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "WrongPass123"
            }
        )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    
    # In debug mode, it might allow without token
    # In production, it should return 401
    assert response.status_code in [401, 403]