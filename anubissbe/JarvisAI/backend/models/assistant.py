from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class CommandType(str, Enum):
    SYSTEM = "system"
    WEB = "web"
    EMAIL = "email"
    CALENDAR = "calendar"
    WEATHER = "weather"
    MUSIC = "music"
    CUSTOM = "custom"

class Command(BaseModel):
    type: CommandType
    action: str
    parameters: Dict[str, Any] = {}

class AssistantResponse(BaseModel):
    text: str
    commands: Optional[List[Command]] = None
    data: Optional[Dict[str, Any]] = None