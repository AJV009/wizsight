"""Control request models for light operations."""

from pydantic import BaseModel, Field, validator


class BrightnessRequest(BaseModel):
    """Request model for brightness control operations.
    
    This model validates parameters for POST /lights/{ip}/brightness endpoint.
    """
    
    brightness: int = Field(
        ...,
        ge=0,
        le=255,
        description="Brightness level to set (0-255). 0 turns the light off.",
        example=150
    )
    
    force_on: bool = Field(
        default=True,
        description="Whether to turn the light on if it's currently off. Defaults to true.",
        example=True
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "brightness": 150,
                "force_on": True
            }
        }


class ColortempRequest(BaseModel):
    """Request model for color temperature control operations.
    
    This model validates parameters for POST /lights/{ip}/colortemp endpoint.
    """
    
    colortemp: int = Field(
        ...,
        ge=1000,
        le=10000,
        description="Color temperature in Kelvin (1000-10000K). Lower values are warmer (more red), higher values are cooler (more blue).",
        example=4000
    )
    
    force_on: bool = Field(
        default=True,
        description="Whether to turn the light on if it's currently off. Defaults to true.",
        example=True
    )
    
    @validator('colortemp')
    def validate_colortemp_practical_range(cls, v):
        """Additional validation for practical color temperature ranges."""
        # While 1000-10000K is the theoretical range, most lights support 2700-6500K
        # We'll allow the full range but could add warnings for extreme values
        if v < 1000:
            raise ValueError('Color temperature must be at least 1000K')
        if v > 10000:
            raise ValueError('Color temperature must not exceed 10000K')
        return v
    
    def is_warm_white(self) -> bool:
        """Check if this is a warm white temperature (< 3500K)."""
        return self.colortemp < 3500
    
    def is_cool_white(self) -> bool:
        """Check if this is a cool white temperature (> 5000K)."""
        return self.colortemp > 5000
    
    def is_neutral_white(self) -> bool:
        """Check if this is a neutral white temperature (3500-5000K)."""
        return 3500 <= self.colortemp <= 5000
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "colortemp": 4000,
                "force_on": True
            }
        }