from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from services.user import UserService
from services.auth import get_current_user, authenticate_user
from models.user import User, UserCreate, UserUpdate

router = APIRouter()
user_service = UserService()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await user_service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(username: str, password: str):
    """Login and get access token"""
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = user_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information"""
    updated_user = await user_service.update_user(current_user.id, user_data)
    return updated_user