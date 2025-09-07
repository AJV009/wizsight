"""Light control service for managing individual WiZ lights."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any

from pywizlight import wizlight, PilotBuilder

from ..models.light_device import LightDevice
from ..models.control_requests import BrightnessRequest, ColortempRequest
from ..models.control_response import ControlResponse
from ..models.error_response import ErrorResponse

logger = logging.getLogger(__name__)


class LightService:
    """Service for controlling individual WiZ lights using pywizlight."""
    
    @staticmethod
    async def toggle_light(ip: str, timeout: float = 3.0) -> ControlResponse:
        """Toggle a light's power state (on -> off, off -> on).
        
        Args:
            ip: IP address of the light to toggle
            timeout: Timeout in seconds for the operation
            
        Returns:
            ControlResponse: Result of the toggle operation
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Toggling light at {ip}")
            
            # Create wizlight instance
            bulb = wizlight(ip)
            
            # Get current state first
            await asyncio.wait_for(bulb.updateState(), timeout=timeout)
            current_state = bulb.state.get_state()
            
            # Toggle the state
            if current_state:
                # Light is on, turn it off
                await asyncio.wait_for(bulb.turn_off(), timeout=timeout)
                new_state = False
                logger.debug(f"Turned off light at {ip}")
            else:
                # Light is off, turn it on
                await asyncio.wait_for(bulb.turn_on(), timeout=timeout)
                new_state = True
                logger.debug(f"Turned on light at {ip}")
            
            # Get response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Get additional device info
            device_info = await LightService._get_device_info(bulb)
            
            return ControlResponse(
                success=True,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="toggle",
                new_state=new_state,
                device_info=device_info
            )
            
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Timeout toggling light at {ip}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="toggle",
                error_code="TIMEOUT",
                error_message=f"Operation timed out after {timeout} seconds"
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to toggle light at {ip}: {e}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="toggle",
                error_code=LightService._map_exception_to_error_code(e),
                error_message=str(e)
            )
    
    @staticmethod
    async def set_brightness(ip: str, request: BrightnessRequest, timeout: float = 3.0) -> ControlResponse:
        """Set the brightness of a light.
        
        Args:
            ip: IP address of the light to control
            request: Brightness control parameters
            timeout: Timeout in seconds for the operation
            
        Returns:
            ControlResponse: Result of the brightness operation
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Setting brightness to {request.brightness} for light at {ip}")
            
            # Create wizlight instance
            bulb = wizlight(ip)
            
            # Get current state
            await asyncio.wait_for(bulb.updateState(), timeout=timeout)
            current_state = bulb.state.get_state()
            
            # Handle brightness = 0 case (turn off)
            if request.brightness == 0:
                await asyncio.wait_for(bulb.turn_off(), timeout=timeout)
                new_state = False
                new_brightness = 0
                logger.debug(f"Turned off light at {ip} (brightness=0)")
            else:
                # Set brightness (this will turn on the light if force_on=True)
                if request.force_on or current_state:
                    await asyncio.wait_for(
                        bulb.turn_on(PilotBuilder(brightness=request.brightness)),
                        timeout=timeout
                    )
                    new_state = True
                    new_brightness = request.brightness
                    logger.debug(f"Set brightness to {request.brightness} for light at {ip}")
                else:
                    # Light is off and force_on=False, just update brightness without turning on
                    # This is a pywizlight limitation - we can't set brightness without turning on
                    # So we return an error in this case
                    response_time_ms = (time.time() - start_time) * 1000
                    return ControlResponse(
                        success=False,
                        target_ip=ip,
                        response_time_ms=response_time_ms,
                        operation="brightness",
                        error_code="INVALID_PARAMETERS",
                        error_message="Cannot set brightness on off light when force_on=False"
                    )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Get additional device info
            device_info = await LightService._get_device_info(bulb)
            
            return ControlResponse(
                success=True,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="brightness",
                new_state=new_state,
                new_brightness=new_brightness,
                device_info=device_info
            )
            
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Timeout setting brightness for light at {ip}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="brightness",
                error_code="TIMEOUT",
                error_message=f"Operation timed out after {timeout} seconds"
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to set brightness for light at {ip}: {e}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="brightness",
                error_code=LightService._map_exception_to_error_code(e),
                error_message=str(e)
            )
    
    @staticmethod
    async def set_colortemp(ip: str, request: ColortempRequest, timeout: float = 3.0) -> ControlResponse:
        """Set the color temperature of a light.
        
        Args:
            ip: IP address of the light to control
            request: Color temperature control parameters
            timeout: Timeout in seconds for the operation
            
        Returns:
            ControlResponse: Result of the color temperature operation
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Setting color temperature to {request.colortemp}K for light at {ip}")
            
            # Create wizlight instance
            bulb = wizlight(ip)
            
            # Get current state
            await asyncio.wait_for(bulb.updateState(), timeout=timeout)
            current_state = bulb.state.get_state()
            
            # Set color temperature
            if request.force_on or current_state:
                await asyncio.wait_for(
                    bulb.turn_on(PilotBuilder(colortemp=request.colortemp)),
                    timeout=timeout
                )
                new_state = True
                new_colortemp = request.colortemp
                logger.debug(f"Set color temperature to {request.colortemp}K for light at {ip}")
            else:
                # Light is off and force_on=False, return error
                response_time_ms = (time.time() - start_time) * 1000
                return ControlResponse(
                    success=False,
                    target_ip=ip,
                    response_time_ms=response_time_ms,
                    operation="colortemp",
                    error_code="INVALID_PARAMETERS",
                    error_message="Cannot set color temperature on off light when force_on=False"
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Get additional device info
            device_info = await LightService._get_device_info(bulb)
            
            return ControlResponse(
                success=True,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="colortemp",
                new_state=new_state,
                new_colortemp=new_colortemp,
                device_info=device_info
            )
            
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.warning(f"Timeout setting color temperature for light at {ip}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="colortemp",
                error_code="TIMEOUT",
                error_message=f"Operation timed out after {timeout} seconds"
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to set color temperature for light at {ip}: {e}")
            
            return ControlResponse(
                success=False,
                target_ip=ip,
                response_time_ms=response_time_ms,
                operation="colortemp",
                error_code=LightService._map_exception_to_error_code(e),
                error_message=str(e)
            )
    
    @staticmethod
    async def get_light_state(ip: str, timeout: float = 3.0) -> Optional[LightDevice]:
        """Get the current state of a light.
        
        Args:
            ip: IP address of the light to query
            timeout: Timeout in seconds for the operation
            
        Returns:
            LightDevice: Current device state, or None if unreachable
        """
        try:
            logger.debug(f"Getting state for light at {ip}")
            
            # Create wizlight instance
            bulb = wizlight(ip)
            
            # Get current state
            await asyncio.wait_for(bulb.updateState(), timeout=timeout)
            
            # Convert to our device model (reuse discovery service logic)
            from .discovery_service import DiscoveryService
            device = await DiscoveryService._bulb_to_light_device(bulb)
            
            logger.debug(f"Retrieved state for light at {ip}")
            return device
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout getting state for light at {ip}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get state for light at {ip}: {e}")
            return None
    
    @staticmethod
    async def _get_device_info(bulb) -> Dict[str, Any]:
        """Get additional device information from a bulb.
        
        Args:
            bulb: pywizlight bulb instance
            
        Returns:
            Dict with device information
        """
        info = {}
        
        try:
            if hasattr(bulb, 'mac') and bulb.mac:
                info['mac'] = str(bulb.mac)
                
            if hasattr(bulb.state, 'get_friendly_name') and bulb.state.get_friendly_name():
                info['name'] = bulb.state.get_friendly_name()
                
            if hasattr(bulb.state, 'get_brightness') and bulb.state.get_brightness() is not None:
                info['current_brightness'] = bulb.state.get_brightness()
                
            if hasattr(bulb.state, 'get_colortemp') and bulb.state.get_colortemp() is not None:
                info['current_colortemp'] = bulb.state.get_colortemp()
                
        except Exception as e:
            logger.debug(f"Failed to get some device info: {e}")
            
        return info
    
    @staticmethod
    def _map_exception_to_error_code(exc: Exception) -> str:
        """Map common exceptions to error codes.
        
        Args:
            exc: Exception to map
            
        Returns:
            String error code
        """
        exc_type = exc.__class__.__name__
        
        error_mapping = {
            'TimeoutError': 'TIMEOUT',
            'ConnectionError': 'NETWORK_ERROR',
            'OSError': 'DEVICE_UNREACHABLE',
            'ValueError': 'INVALID_PARAMETERS',
            'WizLightError': 'DEVICE_ERROR',
        }
        
        # Check if it's a network-related error based on message content
        error_message = str(exc).lower()
        if any(term in error_message for term in ['connection', 'network', 'unreachable', 'refused']):
            return 'NETWORK_ERROR'
        
        return error_mapping.get(exc_type, 'UNKNOWN_ERROR')