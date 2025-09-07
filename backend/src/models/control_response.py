"""Control response model for light operation results."""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator


class ControlResponse(BaseModel):
    """Response model for light control operations.
    
    This model represents the result of toggle, brightness, and colortemp operations.
    """
    
    success: bool = Field(
        ...,
        description="Whether the control operation was successful",
        example=True
    )
    
    target_ip: str = Field(
        ...,
        description="IP address of the target light device",
        example="192.168.1.100"
    )
    
    response_time_ms: float = Field(
        ...,
        ge=0,
        description="Time taken to complete the operation in milliseconds",
        example=245.7
    )
    
    operation: str = Field(
        ...,
        description="Type of operation that was performed",
        example="toggle"
    )
    
    new_state: Optional[bool] = Field(
        None,
        description="New power state of the light (if operation affected power state)",
        example=True
    )
    
    new_brightness: Optional[int] = Field(
        None,
        ge=0,
        le=255,
        description="New brightness level (if brightness was changed)",
        example=150
    )
    
    new_colortemp: Optional[int] = Field(
        None,
        ge=1000,
        le=10000,
        description="New color temperature (if colortemp was changed)",
        example=4000
    )
    
    error_code: Optional[str] = Field(
        None,
        description="Error code if operation failed",
        example="DEVICE_UNREACHABLE"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Human-readable error message if operation failed",
        example="Device at 192.168.1.100 is not responding to network requests"
    )
    
    device_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional device information discovered during operation"
    )
    
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the operation was completed",
        example="2024-01-15T10:30:15Z"
    )
    
    @validator('operation')
    def validate_operation_type(cls, v):
        """Validate operation type."""
        valid_operations = ['toggle', 'brightness', 'colortemp', 'state_query']
        if v not in valid_operations:
            raise ValueError(f'Operation must be one of: {valid_operations}')
        return v
    
    @validator('error_code')
    def validate_error_code(cls, v):
        """Validate error codes."""
        if v is not None:
            valid_codes = [
                'DEVICE_UNREACHABLE',
                'NETWORK_ERROR', 
                'INVALID_PARAMETERS',
                'DEVICE_BUSY',
                'TIMEOUT',
                'UNKNOWN_ERROR'
            ]
            if v not in valid_codes:
                raise ValueError(f'Error code must be one of: {valid_codes}')
        return v
    
    @validator('error_message')
    def validate_error_consistency(cls, v, values):
        """Ensure error message is present if operation failed."""
        if 'success' in values and not values['success']:
            if not v:
                raise ValueError('Error message is required when success=False')
        return v
    
    @validator('new_state')
    def validate_new_state_for_toggle(cls, v, values):
        """For toggle operations, new_state should be present."""
        if 'operation' in values and values['operation'] == 'toggle' and 'success' in values:
            if values['success'] and v is None:
                raise ValueError('new_state is required for successful toggle operations')
        return v
    
    def is_successful(self) -> bool:
        """Check if operation was successful."""
        return self.success
    
    def has_error(self) -> bool:
        """Check if operation resulted in an error."""
        return not self.success or self.error_code is not None
    
    def get_error_details(self) -> Optional[Dict[str, str]]:
        """Get error details if present."""
        if self.has_error():
            return {
                'code': self.error_code or 'UNKNOWN_ERROR',
                'message': self.error_message or 'An unknown error occurred'
            }
        return None
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "success": True,
                "target_ip": "192.168.1.100",
                "response_time_ms": 245.7,
                "operation": "toggle",
                "new_state": True,
                "new_brightness": None,
                "new_colortemp": None,
                "error_code": None,
                "error_message": None,
                "device_info": {
                    "mac": "a4:cf:12:34:56:78",
                    "name": "Living Room Lamp"
                },
                "timestamp": "2024-01-15T10:30:15Z"
            }
        }