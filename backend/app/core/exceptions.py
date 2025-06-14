"""
JarvisAI Custom Exceptions
Centralized exception handling for the application
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class JarvisException(Exception):
    """Base exception class for JarvisAI"""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "internal_error",
        context: Optional[Dict[str, Any]] = None
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        super().__init__(detail)


class AuthenticationError(JarvisException):
    """Authentication related errors"""
    
    def __init__(self, detail: str = "Authentication failed", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="authentication_error",
            context=context
        )


class AuthorizationError(JarvisException):
    """Authorization/permission related errors"""
    
    def __init__(self, detail: str = "Insufficient permissions", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="authorization_error",
            context=context
        )


class ValidationError(JarvisException):
    """Data validation errors"""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="validation_error",
            context=context
        )


class NotFoundError(JarvisException):
    """Resource not found errors"""
    
    def __init__(self, resource: str, identifier: str = "", context: Optional[Dict[str, Any]] = None):
        detail = f"{resource} not found"
        if identifier:
            detail += f": {identifier}"
        
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="not_found_error",
            context=context
        )


class ConflictError(JarvisException):
    """Resource conflict errors"""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_code="conflict_error",
            context=context
        )


class RateLimitError(JarvisException):
    """Rate limiting errors"""
    
    def __init__(self, detail: str = "Rate limit exceeded", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="rate_limit_error",
            context=context
        )


class ServiceUnavailableError(JarvisException):
    """External service unavailable errors"""
    
    def __init__(self, service: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=f"{service} service is currently unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="service_unavailable_error",
            context=context
        )


class ModelError(JarvisException):
    """LLM model related errors"""
    
    def __init__(self, detail: str, model_name: str = "", context: Optional[Dict[str, Any]] = None):
        if model_name:
            detail = f"Model '{model_name}': {detail}"
        
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="model_error",
            context=context
        )


class VectorStoreError(JarvisException):
    """Vector database related errors"""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=f"Vector store error: {detail}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="vector_store_error",
            context=context
        )


class DocumentProcessingError(JarvisException):
    """Document processing related errors"""
    
    def __init__(self, detail: str, filename: str = "", context: Optional[Dict[str, Any]] = None):
        if filename:
            detail = f"Document '{filename}': {detail}"
        
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="document_processing_error",
            context=context
        )


class ConfigurationError(JarvisException):
    """Configuration related errors"""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=f"Configuration error: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="configuration_error",
            context=context
        )


class TherapeuticModeError(JarvisException):
    """Therapeutic mode related errors"""
    
    def __init__(self, detail: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=f"Therapeutic mode error: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="therapeutic_mode_error",
            context=context
        )


class CrisisDetectedError(JarvisException):
    """Crisis situation detected"""
    
    def __init__(self, detail: str = "Crisis situation detected", context: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="crisis_detected_error",
            context=context
        )