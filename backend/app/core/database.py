"""
JarvisAI Database Configuration
SQLAlchemy setup with async PostgreSQL support
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for async
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


async def init_db():
    """Initialize database and create tables"""
    try:
        # Import all models here to ensure they are registered
        from app.models.user import User
        # Additional models will be imported as we create them
        # from app.models.chat import ChatSession, Message
        # from app.models.document import Document
        # from app.models.agent import Agent
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()