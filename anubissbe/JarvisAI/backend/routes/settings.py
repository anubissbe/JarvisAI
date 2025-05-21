from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from services.settings import SettingsService
from services.auth import get_current_user
from models.user import User
from models.settings import Settings, SettingsUpdate

router = APIRouter()
settings_service = SettingsService()

@router.get("/", response_model=Settings)
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get user settings"""
    settings = await settings_service.get_settings(current_user.id)
    return settings

@router.put("/", response_model=Settings)
async def update_settings(
    settings_data: SettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user settings"""
    updated_settings = await settings_service.update_settings(current_user.id, settings_data)
    return updated_settings