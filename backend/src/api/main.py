"""Main FastAPI application for WizSight."""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..models.light_device import LightDevice
from ..models.network_scan import NetworkScan
from ..models.control_requests import BrightnessRequest, ColortempRequest
from ..models.control_response import ControlResponse
from ..models.error_response import ErrorResponse
from ..services.discovery_service import DiscoveryService
from ..services.light_service import LightService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="WizSight API",
    description="API for discovering and controlling WiZ smart lights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
import os
static_dir = os.path.join(os.path.dirname(__file__), "../../../frontend/static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend HTML file."""
    frontend_path = os.path.join(os.path.dirname(__file__), "../../../frontend/static/index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {"message": "WizSight API is running. Frontend not yet available."}

@app.get("/scan", response_model=NetworkScan)
async def scan_for_lights(
    broadcast_address: Optional[str] = Query(
        default="255.255.255.255",
        description="Network broadcast address for discovery",
        example="192.168.1.255"
    ),
    timeout: Optional[float] = Query(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Discovery timeout in seconds",
        example=5.0
    )
):
    """Discover WiZ lights on the network.
    
    This endpoint performs a UDP broadcast discovery to find available WiZ lights
    on the specified network. Returns a list of discovered devices with their
    current state information.
    """
    try:
        # Validate broadcast address
        if not DiscoveryService.validate_broadcast_address(broadcast_address):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid broadcast address format: {broadcast_address}"
            )
        
        logger.info(f"Starting discovery on {broadcast_address} with timeout {timeout}s")
        
        # Perform discovery
        scan_result = await DiscoveryService.discover_lights(
            broadcast_address=broadcast_address,
            timeout=timeout
        )
        
        logger.info(f"Discovery completed: {scan_result.discovered_count} lights found")
        return scan_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(e).model_dump(mode='json')
        )

@app.post("/lights/{ip}/toggle", response_model=ControlResponse)
async def toggle_light(
    ip: str = Path(..., description="IP address of the light to toggle", example="192.168.1.100")
):
    """Toggle a light's power state (on -> off, off -> on).
    
    This endpoint checks the current state of the specified light and switches
    it to the opposite state. If the light is on, it will be turned off.
    If the light is off, it will be turned on.
    """
    try:
        logger.info(f"Toggling light at {ip}")
        
        # Perform toggle operation
        result = await LightService.toggle_light(ip)
        
        if result.success:
            logger.info(f"Successfully toggled light at {ip}: {result.new_state}")
        else:
            logger.warning(f"Failed to toggle light at {ip}: {result.error_message}")
            
            # Map error codes to appropriate HTTP status codes
            if result.error_code == "TIMEOUT":
                raise HTTPException(status_code=408, detail=result.model_dump(mode='json'))
            elif result.error_code in ["DEVICE_UNREACHABLE", "NETWORK_ERROR"]:
                raise HTTPException(status_code=400, detail=result.model_dump(mode='json'))
            else:
                raise HTTPException(status_code=500, detail=result.model_dump(mode='json'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle operation failed for {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(e).model_dump(mode='json')
        )

@app.post("/lights/{ip}/brightness", response_model=ControlResponse)
async def set_brightness(
    request: BrightnessRequest,
    ip: str = Path(..., description="IP address of the light to control", example="192.168.1.100")
):
    """Set the brightness of a light.
    
    Controls the brightness level of the specified light. Brightness value
    ranges from 0 to 255, where 0 turns the light off and 255 is maximum brightness.
    The force_on parameter determines whether to turn the light on if it's currently off.
    """
    try:
        logger.info(f"Setting brightness to {request.brightness} for light at {ip}")
        
        # Perform brightness control
        result = await LightService.set_brightness(ip, request)
        
        if result.success:
            logger.info(f"Successfully set brightness for light at {ip}: {request.brightness}")
        else:
            logger.warning(f"Failed to set brightness for light at {ip}: {result.error_message}")
            
            # Map error codes to HTTP status codes
            if result.error_code == "TIMEOUT":
                raise HTTPException(status_code=408, detail=result.model_dump(mode='json'))
            elif result.error_code in ["DEVICE_UNREACHABLE", "NETWORK_ERROR"]:
                raise HTTPException(status_code=400, detail=result.model_dump(mode='json'))
            elif result.error_code == "INVALID_PARAMETERS":
                raise HTTPException(status_code=400, detail=result.model_dump(mode='json'))
            else:
                raise HTTPException(status_code=500, detail=result.model_dump(mode='json'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Brightness control failed for {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(e).model_dump(mode='json')
        )

@app.post("/lights/{ip}/colortemp", response_model=ControlResponse)
async def set_colortemp(
    request: ColortempRequest,
    ip: str = Path(..., description="IP address of the light to control", example="192.168.1.100")
):
    """Set the color temperature of a light.
    
    Controls the color temperature of the specified light in Kelvin.
    Valid range is 1000K to 10000K, where lower values are warmer (more red/orange)
    and higher values are cooler (more blue/white). The force_on parameter 
    determines whether to turn the light on if it's currently off.
    """
    try:
        logger.info(f"Setting color temperature to {request.colortemp}K for light at {ip}")
        
        # Perform color temperature control
        result = await LightService.set_colortemp(ip, request)
        
        if result.success:
            logger.info(f"Successfully set color temperature for light at {ip}: {request.colortemp}K")
        else:
            logger.warning(f"Failed to set color temperature for light at {ip}: {result.error_message}")
            
            # Map error codes to HTTP status codes
            if result.error_code == "TIMEOUT":
                raise HTTPException(status_code=408, detail=result.model_dump(mode='json'))
            elif result.error_code in ["DEVICE_UNREACHABLE", "NETWORK_ERROR"]:
                raise HTTPException(status_code=400, detail=result.model_dump(mode='json'))
            elif result.error_code == "INVALID_PARAMETERS":
                raise HTTPException(status_code=400, detail=result.model_dump(mode='json'))
            else:
                raise HTTPException(status_code=500, detail=result.model_dump(mode='json'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Color temperature control failed for {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(e).model_dump(mode='json')
        )

@app.get("/lights/{ip}/state", response_model=LightDevice)
async def get_light_state(
    ip: str = Path(..., description="IP address of the light to query", example="192.168.1.100")
):
    """Get the current state of a light.
    
    Retrieves the current state information for the specified light, including
    power state, brightness, color temperature, and other available properties.
    """
    try:
        logger.debug(f"Getting state for light at {ip}")
        
        # Get light state
        device = await LightService.get_light_state(ip)
        
        if device is None:
            logger.warning(f"Light at {ip} is not reachable")
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse.device_unreachable(ip).model_dump(mode='json')
            )
        
        if not device.available:
            logger.warning(f"Light at {ip} is not available")
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse.device_unreachable(ip).model_dump(mode='json')
            )
        
        logger.debug(f"Retrieved state for light at {ip}")
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get state for light at {ip}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse.from_exception(e).model_dump(mode='json')
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "WizSight API"}

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )