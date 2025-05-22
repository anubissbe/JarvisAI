# ... existing code ...

from models.db.user import UserDB
from models.db.settings import SettingsDB
from models.db.document import DocumentDB

# ... existing code ...

async def init_db():
    """Initialize the database connection"""
    try:
        await init_beanie(
            database=db,
            document_models=[
                UserDB,
                SettingsDB,
                DocumentDB
            ]
        )
        logger.info("Database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise