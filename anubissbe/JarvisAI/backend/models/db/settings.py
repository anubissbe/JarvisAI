from beanie import Document
from pydantic import Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class VoiceSettingsDB(Document):
    enabled: bool = True
    voice_id: str = "en-US-Standard-B"
    speed: float = 1.0
    pitch: float = 0.0

class AIModelSettingsDB(Document):
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 150

class IntegrationSettingsDB(Document):
    enabled_integrations: List[str] = []
    api_keys: Dict[str, str] = {}

class SettingsDB(Document):
    user_id: str
    voice: VoiceSettingsDB = Field(default_factory=VoiceSettingsDB)
    ai_model: AIModelSettingsDB = Field(default_factory=AIModelSettingsDB)
    integrations: IntegrationSettingsDB = Field(default_factory=IntegrationSettingsDB)
    theme: str = "dark"
    custom_settings: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "settings"