from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from datetime import datetime

class UserDB(Document):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"