"""
JarvisAI Configuration Management
Centralized configuration using Pydantic Settings
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    APP_NAME: str = "JarvisAI"
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS and Hosts
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        env="ALLOWED_HOSTS"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # Ollama Configuration
    OLLAMA_HOST: str = Field(default="http://ollama:11434", env="OLLAMA_HOST")
    OLLAMA_TIMEOUT: int = Field(default=300, env="OLLAMA_TIMEOUT")
    OLLAMA_MAX_RETRIES: int = Field(default=3, env="OLLAMA_MAX_RETRIES")
    
    # Qdrant Configuration
    QDRANT_HOST: str = Field(default="qdrant", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_TIMEOUT: int = Field(default=60, env="QDRANT_TIMEOUT")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = Field(default="minio:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(..., env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(..., env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")
    MINIO_BUCKET_NAME: str = Field(default="jarvis-documents", env="MINIO_BUCKET_NAME")
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None, env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None, env="GITHUB_CLIENT_SECRET")
    
    # OpenAI API (for compatibility/fallback)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    
    # LangChain/LangGraph
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    LANGCHAIN_TRACING_V2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    
    # File Upload Limits
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".pdf", ".docx", ".txt", ".md", ".pptx", ".xlsx"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # RAG Configuration
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-m3", env="EMBEDDING_MODEL")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    MAX_RETRIEVED_DOCS: int = Field(default=5, env="MAX_RETRIEVED_DOCS")
    
    # Monitoring & Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Model Configuration
    DEFAULT_MODEL: str = Field(default="llama3.1:8b", env="DEFAULT_MODEL")
    SUPPORTED_MODELS: List[str] = Field(
        default=[
            "llama3.1:8b",
            "deepseek-r1:14b", 
            "mistral:7b",
            "codellama:13b",
            "qwen2.5:7b"
        ],
        env="SUPPORTED_MODELS"
    )
    
    # Therapeutic Mode Configuration
    THERAPEUTIC_MODE_ENABLED: bool = Field(default=True, env="THERAPEUTIC_MODE_ENABLED")
    THERAPEUTIC_MODEL: str = Field(default="llama3.1:8b", env="THERAPEUTIC_MODEL")
    CRISIS_KEYWORDS: List[str] = Field(
        default=["suicide", "self-harm", "kill myself", "end it all"],
        env="CRISIS_KEYWORDS"
    )
    
    @validator("CORS_ORIGINS", "ALLOWED_HOSTS", "ALLOWED_FILE_TYPES", 
              "SUPPORTED_MODELS", "CRISIS_KEYWORDS", pre=True)
    def parse_list_from_string(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()