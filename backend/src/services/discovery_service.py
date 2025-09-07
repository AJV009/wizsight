"""Discovery service for finding WiZ lights on the network."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone

from pywizlight import discovery

from ..models.light_device import LightDevice
from ..models.network_scan import NetworkScan
from ..models.error_response import ErrorResponse

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for discovering WiZ lights on the network using pywizlight."""
    
    @staticmethod
    async def discover_lights(
        broadcast_address: str = "255.255.255.255",
        timeout: float = 5.0
    ) -> NetworkScan:
        """Discover WiZ lights on the network.
        
        Args:
            broadcast_address: Network broadcast address for discovery
            timeout: Timeout in seconds for the discovery operation
            
        Returns:
            NetworkScan: Results of the discovery operation
            
        Raises:
            Exception: If discovery fails due to network or other errors
        """
        scan_start = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Starting light discovery on {broadcast_address} with {timeout}s timeout")
            
            # Use pywizlight discovery with custom broadcast address and timeout
            discovered_bulbs = await discovery.discover_lights(
                broadcast_space=broadcast_address,
                wait_time=timeout
            )
            
            # Convert discovered bulbs to our LightDevice models
            devices = []
            for bulb in discovered_bulbs:
                try:
                    # Get current state of each discovered light
                    device = await DiscoveryService._bulb_to_light_device(bulb)
                    devices.append(device)
                    logger.debug(f"Discovered light at {bulb.ip}")
                except Exception as e:
                    logger.warning(f"Failed to get state for light at {bulb.ip}: {e}")
                    # Create a basic device entry even if state query fails
                    devices.append(LightDevice(
                        ip=str(bulb.ip),
                        state=False,
                        available=False,
                        last_seen=datetime.now(timezone.utc)
                    ))
            
            scan_complete = datetime.now(timezone.utc)
            
            scan_result = NetworkScan(
                status="completed",
                discovered_count=len(devices),
                devices=devices,
                started_at=scan_start,
                completed_at=scan_complete,
                broadcast_address=broadcast_address,
                timeout=timeout
            )
            
            logger.info(f"Discovery completed: found {len(devices)} lights in {scan_result.duration_seconds():.2f}s")
            return scan_result
            
        except asyncio.TimeoutError:
            logger.warning(f"Discovery timeout after {timeout}s on {broadcast_address}")
            scan_complete = datetime.now(timezone.utc)
            
            return NetworkScan(
                status="timeout",
                discovered_count=0,
                devices=[],
                started_at=scan_start,
                completed_at=scan_complete,
                broadcast_address=broadcast_address,
                timeout=timeout
            )
            
        except Exception as e:
            logger.error(f"Discovery failed on {broadcast_address}: {e}")
            scan_complete = datetime.now(timezone.utc)
            
            return NetworkScan(
                status="failed",
                discovered_count=0,
                devices=[],
                started_at=scan_start,
                completed_at=scan_complete,
                broadcast_address=broadcast_address,
                timeout=timeout
            )
    
    @staticmethod
    async def _bulb_to_light_device(bulb) -> LightDevice:
        """Convert a pywizlight bulb object to our LightDevice model.
        
        Args:
            bulb: pywizlight bulb object
            
        Returns:
            LightDevice: Converted device with current state
        """
        try:
            # Get current state from the bulb
            await bulb.updateState()
            
            # Extract state information
            device_data = {
                "ip": str(bulb.ip),
                "available": True,
                "state": bulb.state.get_state() if hasattr(bulb.state, 'get_state') else False,
                "last_seen": datetime.now(timezone.utc)
            }
            
            # Add optional fields if available
            if hasattr(bulb.state, 'get_brightness') and bulb.state.get_brightness() is not None:
                device_data["brightness"] = bulb.state.get_brightness()
                
            if hasattr(bulb.state, 'get_colortemp') and bulb.state.get_colortemp() is not None:
                device_data["colortemp"] = bulb.state.get_colortemp()
                
            if hasattr(bulb.state, 'get_rgb') and bulb.state.get_rgb() is not None:
                rgb = bulb.state.get_rgb()
                if rgb:
                    device_data["rgb"] = list(rgb)
                    
            if hasattr(bulb.state, 'get_scene') and bulb.state.get_scene() is not None:
                device_data["scene"] = bulb.state.get_scene()
                
            if hasattr(bulb, 'mac') and bulb.mac:
                device_data["mac"] = str(bulb.mac)
                
            # Try to get friendly name if available
            if hasattr(bulb.state, 'get_friendly_name') and bulb.state.get_friendly_name():
                device_data["name"] = bulb.state.get_friendly_name()
            
            return LightDevice(**device_data)
            
        except Exception as e:
            logger.warning(f"Failed to get detailed state for {bulb.ip}: {e}")
            # Return basic device info even if state query fails
            return LightDevice(
                ip=str(bulb.ip),
                state=False,
                available=False,
                last_seen=datetime.now(timezone.utc)
            )
    
    @staticmethod
    async def discover_single_light(ip: str, timeout: float = 3.0) -> Optional[LightDevice]:
        """Discover and get state for a single light by IP address.
        
        Args:
            ip: IP address of the light to query
            timeout: Timeout in seconds for the operation
            
        Returns:
            LightDevice: Device information if found and reachable, None otherwise
        """
        try:
            logger.debug(f"Querying single light at {ip}")
            
            # Import wizlight here to avoid circular imports
            from pywizlight import wizlight
            
            # Create wizlight instance for this IP
            bulb = wizlight(ip)
            
            # Try to get current state with timeout
            await asyncio.wait_for(bulb.updateState(), timeout=timeout)
            
            # Convert to our device model
            device = await DiscoveryService._bulb_to_light_device(bulb)
            logger.debug(f"Successfully queried light at {ip}")
            
            return device
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout querying light at {ip}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to query light at {ip}: {e}")
            return None
    
    @staticmethod
    def validate_broadcast_address(address: str) -> bool:
        """Validate if a broadcast address is properly formatted.
        
        Args:
            address: Broadcast address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            import ipaddress
            ipaddress.ip_address(address)
            return True
        except ValueError:
            return False