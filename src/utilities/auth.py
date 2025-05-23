"""
Authentication utilities for Jarvis AI Assistant.
Handles API key validation and user authentication.
"""

import os
import time
import logging
import secrets
import hashlib
import json
from typing import Dict, Optional, List, Any, Tuple
from fastapi import Request, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader

# Set up logging
logger = logging.getLogger("jarvis.utilities.auth")

# API key security scheme
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

class ApiKeyAuth:
    """API key authentication manager for Jarvis API."""
    
    def __init__(self, keys_file: Optional[str] = None):
        """Initialize the API key authentication manager.
        
        Args:
            keys_file: Optional path to a file containing API keys.
        """
        self.keys_file = keys_file or os.path.expanduser("~/.jarvis/api_keys.json")
        self.api_keys = self._load_api_keys()
        self.auth_enabled = self._check_auth_enabled()
        logger.info(f"API Authentication {'enabled' if self.auth_enabled else 'disabled'}")
    
    def _check_auth_enabled(self) -> bool:
        """Check if API authentication is enabled based on environment variable.
        
        Returns:
            True if authentication is enabled, False otherwise.
        """
        # Check environment variable, default to True for production safety
        auth_env = os.environ.get("JARVIS_API_AUTH_ENABLED", "true").lower()
        return auth_env not in ("false", "0", "no", "off")
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from the keys file.
        
        Returns:
            A dictionary of API keys and their metadata.
        """
        try:
            if os.path.exists(self.keys_file):
                with open(self.keys_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.keys_file), exist_ok=True)
                
                # Create default keys if no keys file exists
                default_keys = {
                    "api_keys": {
                        "default": "development_key"
                    },
                    "admin_api_keys": {
                        "admin": "admin_development_key"
                    }
                }
                # Save the default keys
                with open(self.keys_file, 'w', encoding='utf-8') as f:
                    json.dump(default_keys, f, indent=2)
                return default_keys
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}
    
    def save_api_keys(self) -> bool:
        """Save API keys to the keys file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.keys_file, 'w', encoding='utf-8') as f:
                json.dump(self.api_keys, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
            return False
    
    def generate_api_key(self, name: str, role: str = "user") -> Dict[str, Dict[str, Any]]:
        """Generate a new API key.
        
        Args:
            name: A name to associate with the key.
            role: The role for this key (admin or user).
            
        Returns:
            A dictionary containing the new API key.
        """
        # Generate a random key
        api_key = secrets.token_hex(16)
        
        # Add the key to the dictionary
        self.api_keys[api_key] = {
            "name": name,
            "role": role,
            "created": time.time(),
            "last_used": None
        }
        
        # Save the updated keys
        self.save_api_keys()
        
        return self.api_keys
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate an API key.
        
        Args:
            api_key: The API key to validate.
            
        Returns:
            A tuple of (is_valid, key_metadata).
        """
        # If auth is disabled, always return valid
        if not self.auth_enabled:
            return True, {"name": "anonymous", "role": "user"}
            
        # Check if this is a development key
        if api_key == "development_key":
            return True, {"name": "default", "role": "user"}
        if api_key == "admin_development_key":
            return True, {"name": "admin", "role": "admin"}
            
        # Check if the key exists
        key_data = self.api_keys.get(api_key)
        if not key_data:
            return False, None
        
        # Update last used timestamp
        key_data["last_used"] = time.time()
        self.api_keys[api_key] = key_data
        
        # Save periodically (not on every request to avoid performance issues)
        if int(key_data["last_used"]) % 10 == 0:  # Save roughly every 10 seconds of activity
            self.save_api_keys()
        
        return True, key_data
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key.
        
        Args:
            api_key: The API key to revoke.
            
        Returns:
            True if the key was revoked, False otherwise.
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            self.save_api_keys()
            return True
        return False

    async def validate_api_key_dependency(self, api_key: str = Security(API_KEY_HEADER)) -> Dict[str, Any]:
        """FastAPI dependency for validating API keys.
        
        Args:
            api_key: The API key from the request header.
            
        Returns:
            The key metadata if valid.
            
        Raises:
            HTTPException: If the API key is invalid.
        """
        # If auth is disabled, allow access
        if not self.auth_enabled:
            return {"name": "anonymous", "role": "user"}
        
        if not api_key:
            # During development, use default key
            api_key = "development_key"
        
        # Check if it's a default key
        if api_key == "development_key":
            return {"name": "default", "role": "user"}
        if api_key == "admin_development_key":
            return {"name": "admin", "role": "admin"}
        
        # For non-default keys, validate normally
        is_valid, key_data = self.validate_api_key(api_key)
        if not is_valid or not key_data:
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        return key_data


# Create a global instance for use in FastAPI
api_key_auth = ApiKeyAuth()

# Dependency to use in FastAPI routes
async def get_api_key(api_key: str = Security(API_KEY_HEADER)) -> Dict[str, Any]:
    """FastAPI dependency for getting a validated API key.
    
    Args:
        api_key: The API key from the request header.
        
    Returns:
        The key metadata if valid.
        
    Raises:
        HTTPException: If the API key is invalid.
    """
    return await api_key_auth.validate_api_key_dependency(api_key)


async def get_admin_api_key(key_data: Dict[str, Any] = Depends(get_api_key)) -> Dict[str, Any]:
    """FastAPI dependency for ensuring the API key has admin role.
    
    Args:
        key_data: The validated key data from get_api_key.
        
    Returns:
        The key metadata if valid and has admin role.
        
    Raises:
        HTTPException: If the API key doesn't have admin role.
    """
    if key_data.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required",
        )
    return key_data