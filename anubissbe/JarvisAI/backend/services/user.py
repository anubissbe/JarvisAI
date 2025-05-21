import uuid
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging

from models.user import User, UserCreate, UserUpdate
from .auth import get_password_hash, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if username or email already exists
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("Username already exists")
        
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user object
        user = User(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now
        )
        
        # Save user to database
        await self._save_user(user)
        
        # Create default settings for the user
        from .settings import SettingsService
        settings_service = SettingsService()
        await settings_service.create_default_settings(user_id)
        
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        # In a real implementation, this would query a database
        # For now, we'll use a mock implementation
        try:
            # Mock implementation - replace with actual database query
            # This is just a placeholder
            return None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        # Mock implementation - replace with actual database query
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        # Mock implementation - replace with actual database query
        return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update a user"""
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update fields if provided
        if user_data.email is not None:
            user.email = user_data.email
        
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        
        user.updated_at = datetime.utcnow()
        
        # Save updated user
        await self._save_user(user)
        
        return user
    
    def create_access_token(self, user: User) -> str:
        """Create an access token for a user"""
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user.id}
        token = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return token
    
    async def _save_user(self, user: User) -> None:
        """Save a user to the database"""
        # In a real implementation, this would save to a database
        # For now, we'll use a mock implementation
        pass