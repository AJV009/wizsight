"""NetworkScan model for representing light discovery results."""

from typing import List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator
import uuid

from .light_device import LightDevice


class NetworkScan(BaseModel):
    """Represents the results of a network scan for WiZ lights.
    
    This model matches the API specification for the /scan endpoint response.
    """
    
    scan_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this scan operation",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    status: str = Field(
        ...,
        description="Status of the scan operation",
        example="completed"
    )
    
    discovered_count: int = Field(
        ...,
        ge=0,
        description="Number of lights discovered during the scan",
        example=3
    )
    
    devices: List[LightDevice] = Field(
        default_factory=list,
        description="List of discovered light devices with their current state"
    )
    
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the scan was initiated",
        example="2024-01-15T10:30:00Z"
    )
    
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the scan was completed",
        example="2024-01-15T10:30:05Z"
    )
    
    broadcast_address: str = Field(
        default="255.255.255.255",
        description="Broadcast address used for discovery",
        example="192.168.1.255"
    )
    
    timeout: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Timeout in seconds used for the scan",
        example=5.0
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate scan status values."""
        valid_statuses = ['in_progress', 'completed', 'failed', 'timeout']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v
    
    @validator('devices')
    def validate_device_count_matches(cls, v, values):
        """Ensure discovered_count matches the actual device list length."""
        if 'discovered_count' in values:
            if len(v) != values['discovered_count']:
                raise ValueError('discovered_count must match the number of devices')
        return v
    
    @validator('completed_at')
    def validate_completion_time(cls, v, values):
        """Ensure completed_at is after started_at."""
        if 'started_at' in values and v < values['started_at']:
            raise ValueError('completed_at must be after started_at')
        return v
    
    @validator('broadcast_address')
    def validate_broadcast_address(cls, v):
        """Validate broadcast address format."""
        import ipaddress
        try:
            # Check if it's a valid IP address
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid broadcast address format')
    
    def duration_seconds(self) -> float:
        """Calculate scan duration in seconds."""
        return (self.completed_at - self.started_at).total_seconds()
    
    def is_completed(self) -> bool:
        """Check if scan has completed successfully."""
        return self.status == 'completed'
    
    def has_devices(self) -> bool:
        """Check if any devices were discovered."""
        return self.discovered_count > 0
    
    def get_available_devices(self) -> List[LightDevice]:
        """Get only the devices that are currently available."""
        return [device for device in self.devices if device.available]
    
    def get_unavailable_devices(self) -> List[LightDevice]:
        """Get only the devices that are currently unavailable."""
        return [device for device in self.devices if not device.available]
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "discovered_count": 2,
                "devices": [
                    {
                        "ip": "192.168.1.100",
                        "state": True,
                        "available": True,
                        "brightness": 200,
                        "colortemp": 4000,
                        "name": "Living Room Lamp"
                    },
                    {
                        "ip": "192.168.1.101", 
                        "state": False,
                        "available": True,
                        "brightness": 0,
                        "name": "Bedroom Light"
                    }
                ],
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:30:05Z",
                "broadcast_address": "192.168.1.255",
                "timeout": 5.0
            }
        }