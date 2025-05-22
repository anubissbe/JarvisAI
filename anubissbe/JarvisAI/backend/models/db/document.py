from beanie import Document
from pydantic import Field
from typing import List, Optional
from datetime import datetime

class DocumentDB(Document):
    user_id: str
    title: str
    content: str
    file_type: str  # pdf, txt, etc.
    original_filename: str
    embedding_status: str = "pending"  # pending, processing, completed, failed
    chunks: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "documents"