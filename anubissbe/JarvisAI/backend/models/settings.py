from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class VoiceSettings(BaseModel):
    enabled: bool = True
    voice_id: str = "en-US-Standard-B"
    speed: float = 1.0
    pitch: float = 0.0

class AIModelSettings(BaseModel):
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 150

class IntegrationSettings(BaseModel):
    enabled_integrations: List[str] = []
    api_keys: Dict[str, str] = {}

class Settings(BaseModel):
    user_id: str
    voice: VoiceSettings = VoiceSettings()
    ai_model: AIModelSettings = AIModelSettings()
    integrations: IntegrationSettings = IntegrationSettings()
    theme: str = "dark"
    custom_settings: Dict[str, Any] = {}

class SettingsUpdate(BaseModel):
    voice: Optional[VoiceSettings] = None
    ai_model: Optional[AIModelSettings] = None
    integrations: Optional[IntegrationSettings] = None
    theme: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None