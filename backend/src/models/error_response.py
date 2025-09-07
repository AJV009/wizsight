"""Error response model for API error handling."""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model for API endpoints.
    
    This model provides consistent error reporting across all endpoints.
    """
    
    error: str = Field(
        ...,
        description="Error code or category",
        example="DEVICE_UNREACHABLE"
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="The light at 192.168.1.100 is not responding to network requests"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context and debugging information"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the error occurred",
        example="2024-01-15T10:30:00Z"
    )
    
    request_id: Optional[str] = Field(
        None,
        description="Unique identifier for the request that caused this error",
        example="req_550e8400-e29b-41d4-a716-446655440000"
    )
    
    def __init__(self, error: str, message: str, **kwargs):
        """Initialize error response with required fields."""
        super().__init__(error=error, message=message, **kwargs)
    
    @classmethod
    def device_unreachable(cls, ip: str, **kwargs) -> 'ErrorResponse':
        """Create error for unreachable device."""
        return cls(
            error="DEVICE_UNREACHABLE",
            message=f"Device at {ip} is not responding to network requests",
            details={"target_ip": ip},
            **kwargs
        )
    
    @classmethod
    def network_error(cls, message: str = "Network communication failed", **kwargs) -> 'ErrorResponse':
        """Create error for network issues."""
        return cls(
            error="NETWORK_ERROR", 
            message=message,
            **kwargs
        )
    
    @classmethod
    def invalid_parameters(cls, message: str = "Invalid request parameters", **kwargs) -> 'ErrorResponse':
        """Create error for parameter validation failures."""
        return cls(
            error="INVALID_PARAMETERS",
            message=message,
            **kwargs
        )
    
    @classmethod
    def timeout_error(cls, timeout_seconds: float, **kwargs) -> 'ErrorResponse':
        """Create error for timeout scenarios."""
        return cls(
            error="TIMEOUT",
            message=f"Operation timed out after {timeout_seconds} seconds",
            details={"timeout_seconds": timeout_seconds},
            **kwargs
        )
    
    @classmethod
    def device_busy(cls, ip: str, **kwargs) -> 'ErrorResponse':
        """Create error for device busy scenarios."""
        return cls(
            error="DEVICE_BUSY",
            message=f"Device at {ip} is currently busy with another operation",
            details={"target_ip": ip},
            **kwargs
        )
    
    @classmethod
    def unknown_error(cls, message: str = "An unexpected error occurred", **kwargs) -> 'ErrorResponse':
        """Create error for unknown/unexpected errors."""
        return cls(
            error="UNKNOWN_ERROR",
            message=message,
            **kwargs
        )
    
    @classmethod
    def from_exception(cls, exc: Exception, **kwargs) -> 'ErrorResponse':
        """Create error response from an exception."""
        error_type = exc.__class__.__name__
        
        # Map common exception types to error codes
        error_mapping = {
            'TimeoutError': 'TIMEOUT',
            'ConnectionError': 'NETWORK_ERROR',
            'ValueError': 'INVALID_PARAMETERS',
            'OSError': 'NETWORK_ERROR',
        }
        
        error_code = error_mapping.get(error_type, 'UNKNOWN_ERROR')
        
        return cls(
            error=error_code,
            message=str(exc) or f"An error occurred: {error_type}",
            details={
                'exception_type': error_type,
                'exception_message': str(exc)
            },
            **kwargs
        )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "error": "DEVICE_UNREACHABLE",
                "message": "Device at 192.168.1.100 is not responding to network requests",
                "details": {
                    "target_ip": "192.168.1.100",
                    "last_seen": "2024-01-15T09:45:00Z"
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req_550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Extended error response for validation failures with field details."""
    
    error: str = Field(default="VALIDATION_ERROR", description="Error type")
    message: str = Field(..., description="Human-readable error message") 
    validation_errors: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed validation error information"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_pydantic_error(cls, validation_error, **kwargs) -> 'ValidationErrorResponse':
        """Create validation error from Pydantic ValidationError."""
        errors = []
        for error in validation_error.errors():
            errors.append({
                'field': '.'.join(str(loc) for loc in error['loc']),
                'message': error['msg'],
                'type': error['type'],
                'input': error.get('input')
            })
        
        return cls(
            message=f"Validation failed for {len(errors)} field(s)",
            validation_errors=errors,
            **kwargs
        )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }