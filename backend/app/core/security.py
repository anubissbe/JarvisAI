"""
Security utilities for JarvisAI
JWT token creation, validation, and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities for authentication and authorization"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password for storing"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        logger.debug("Access token created", user_id=data.get("sub"))
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time (default: 30 days)
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        logger.debug("Refresh token created", user_id=data.get("sub"))
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning("JWT decode error", error=str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error decoding token", error=str(e))
            return None
    
    @staticmethod
    def validate_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token and check its type
        
        Args:
            token: JWT token to validate
            token_type: Expected token type (access or refresh)
            
        Returns:
            Token payload if valid, None otherwise
        """
        payload = SecurityUtils.decode_token(token)
        
        if not payload:
            return None
        
        # Check token type
        if payload.get("type") != token_type:
            logger.warning(
                "Invalid token type",
                expected=token_type,
                received=payload.get("type")
            )
            return None
        
        # Check expiration (already done by jwt.decode, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            logger.info("Token expired", user_id=payload.get("sub"))
            return None
        
        return payload
    
    @staticmethod
    def extract_token_from_bearer(authorization: str) -> Optional[str]:
        """
        Extract token from Bearer authorization header
        
        Args:
            authorization: Authorization header value
            
        Returns:
            Extracted token or None
        """
        if not authorization:
            return None
        
        parts = authorization.split()
        
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Invalid authorization header format")
            return None
        
        return parts[1]
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key for service-to-service auth"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_api_key(api_key: str, stored_hash: str) -> bool:
        """Validate an API key against its stored hash"""
        return SecurityUtils.verify_password(api_key, stored_hash)


# Convenience functions
verify_password = SecurityUtils.verify_password
get_password_hash = SecurityUtils.get_password_hash
create_access_token = SecurityUtils.create_access_token
create_refresh_token = SecurityUtils.create_refresh_token
decode_token = SecurityUtils.decode_token
validate_token = SecurityUtils.validate_token
extract_token_from_bearer = SecurityUtils.extract_token_from_bearer