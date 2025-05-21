import os
import motor.motor_asyncio
from beanie import init_beanie
import logging

from models.db.user import UserDB
from models.db.settings import SettingsDB

logger = logging.getLogger(__name__)

# MongoDB connection string
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "jarvis_ai")

# MongoDB client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

async def init_db():
    """Initialize the database connection"""
    try:
        await init_beanie(
            database=db,
            document_models=[
                UserDB,
                SettingsDB
            ]
        )
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise