"""LightDevice model for representing WiZ light state and properties."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, IPvAnyAddress


class LightDevice(BaseModel):
    """Represents a discovered or controlled WiZ light device.
    
    This model matches the API specification and maps to pywizlight data.
    """
    
    ip: str = Field(
        ...,
        description="IP address of the light device",
        example="192.168.1.100"
    )
    
    state: bool = Field(
        ...,
        description="Power state of the light (on/off)",
        example=True
    )
    
    available: bool = Field(
        ...,
        description="Whether the light is currently reachable on the network",
        example=True
    )
    
    brightness: Optional[int] = Field(
        None,
        ge=0,
        le=255,
        description="Current brightness level (0-255). Only present if light is on.",
        example=128
    )
    
    colortemp: Optional[int] = Field(
        None,
        ge=1000,
        le=10000,
        description="Color temperature in Kelvin (1000-10000K). Only present in white light mode.",
        example=4000
    )
    
    rgb: Optional[List[int]] = Field(
        None,
        description="RGB color values [R, G, B] (0-255 each). Only present in color mode.",
        example=[255, 128, 0]
    )
    
    scene: Optional[int] = Field(
        None,
        ge=1,
        le=37,
        description="Active scene ID (1-37) if light is in scene mode.",
        example=12
    )
    
    mac: Optional[str] = Field(
        None,
        description="MAC address of the light device",
        example="a4:cf:12:34:56:78"
    )
    
    name: Optional[str] = Field(
        None,
        description="User-assigned name of the light",
        example="Living Room Lamp"
    )
    
    last_seen: Optional[datetime] = Field(
        None,
        description="Last time the device responded to network queries",
        example="2024-01-15T10:30:00Z"
    )
    
    @validator('ip')
    def validate_ip_address(cls, v):
        """Validate that IP address is properly formatted."""
        try:
            IPvAnyAddress(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')
    
    @validator('rgb')
    def validate_rgb_values(cls, v):
        """Validate RGB color values."""
        if v is not None:
            if len(v) != 3:
                raise ValueError('RGB must contain exactly 3 values')
            for value in v:
                if not isinstance(value, int) or not (0 <= value <= 255):
                    raise ValueError('RGB values must be integers between 0-255')
        return v
    
    @validator('mac')
    def validate_mac_address(cls, v):
        """Validate MAC address format."""
        if v is not None:
            import re
            if not re.match(r'^([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}$', v):
                raise ValueError('Invalid MAC address format')
        return v
    
    def is_color_mode(self) -> bool:
        """Check if light is currently in RGB color mode."""
        return self.rgb is not None and any(value > 0 for value in self.rgb)
    
    def is_white_mode(self) -> bool:
        """Check if light is currently in white/color temperature mode."""
        return self.colortemp is not None and self.colortemp > 0
    
    def is_scene_mode(self) -> bool:
        """Check if light is currently displaying a scene."""
        return self.scene is not None and self.scene > 0
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "ip": "192.168.1.100",
                "state": True,
                "available": True,
                "brightness": 200,
                "colortemp": 4000,
                "rgb": None,
                "scene": None,
                "mac": "a4:cf:12:34:56:78",
                "name": "Living Room Lamp",
                "last_seen": "2024-01-15T10:30:00Z"
            }
        }