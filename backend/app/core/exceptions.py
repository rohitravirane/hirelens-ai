"""
Custom exception classes for the application
"""
from typing import Optional, Dict, Any


class HireLensException(Exception):
    """Base exception for HireLens AI"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(HireLensException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(HireLensException):
    """Authorization/permission errors"""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(HireLensException):
    """Resource not found errors"""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ValidationError(HireLensException):
    """Validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class ProcessingError(HireLensException):
    """File/resume processing errors"""
    
    def __init__(self, message: str = "Processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class AIEngineError(HireLensException):
    """AI engine related errors"""
    
    def __init__(self, message: str = "AI processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

