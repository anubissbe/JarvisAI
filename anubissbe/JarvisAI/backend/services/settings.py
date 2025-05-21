import logging
from typing import Optional
from models.settings import Settings, SettingsUpdate

logger = logging.getLogger(__name__)

class SettingsService:
    async def get_settings(self, user_id: str) -> Settings:
        """Get settings for a user"""
        try:
            # In a real implementation, this would query a database
            # For now, return default settings
            return Settings(user_id=user_id)
        except Exception as e:
            logger.error(f"Error getting settings: {str(e)}")
            # Return default settings if there's an error
            return Settings(user_id=user_id)
    
    async def update_settings(self, user_id: str, settings_data: SettingsUpdate) -> Settings:
        """Update settings for a user"""
        try:
            # Get current settings
            current_settings = await self.get_settings(user_id)
            
            # Update fields if provided
            if settings_data.voice is not None:
                current_settings.voice = settings_data.voice
            
            if settings_data.ai_model is not None:
                current_settings.ai_model = settings_data.ai_model
            
            if settings_data.integrations is not None:
                current_settings.integrations = settings_data.integrations
            
            if settings_data.theme is not None:
                current_settings.theme = settings_data.theme
            
            if settings_data.custom_settings is not None:
                current_settings.custom_settings = settings_data.custom_settings
            
            # Save updated settings
            await self._save_settings(current_settings)
            
            return current_settings
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            raise
    
    async def create_default_settings(self, user_id: str) -> Settings:
        """Create default settings for a new user"""
        settings = Settings(user_id=user_id)
        await self._save_settings(settings)
        return settings
    
    async def _save_settings(self, settings: Settings) -> None:
        """Save settings to the database"""
        # In a real implementation, this would save to a database
        # For now, we'll use a mock implementation
        pass