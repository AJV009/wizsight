"""
Integration test for light discovery workflow.

This test validates the complete discovery flow from API to pywizlight.
It MUST FAIL until the full discovery implementation is complete.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status


@pytest.fixture
async def client():
    """Create test client for the FastAPI application."""
    from src.api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestLightDiscoveryIntegration:
    """Integration tests for complete light discovery workflow."""

    async def test_discovery_end_to_end_flow(self, client: AsyncClient):
        """Test complete discovery flow from API call to response."""
        # Step 1: Initiate discovery
        response = await client.get("/scan")
        
        # Should complete successfully (even if no lights found)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "scan_id" in data
        assert "status" in data
        assert data["status"] in ["completed", "in_progress"]
        
        # Step 2: If in progress, should eventually complete
        if data["status"] == "in_progress":
            # In a real implementation, might need to poll or wait
            # For now, just ensure the response format is correct
            assert "discovered_count" in data
            
        # Step 3: Validate discovery results format
        assert isinstance(data["discovered_count"], int)
        assert data["discovered_count"] >= 0
        assert isinstance(data["devices"], list)
        assert len(data["devices"]) == data["discovered_count"]

    async def test_discovery_with_real_network_scan(self, client: AsyncClient):
        """Test discovery using actual network broadcast."""
        # Use default network broadcast
        response = await client.get("/scan")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should have proper scan metadata
        assert "scan_id" in data
        assert len(data["scan_id"]) > 0  # Should be a valid UUID or identifier
        
        # Should track timing
        assert "completed_at" in data or "status" in data
        
        # Each discovered device should have required fields
        for device in data["devices"]:
            assert "ip" in device
            assert "available" in device
            assert "state" in device
            
            # IP should be valid format (basic check)
            ip_parts = device["ip"].split(".")
            assert len(ip_parts) == 4
            for part in ip_parts:
                assert 0 <= int(part) <= 255

    async def test_discovery_custom_broadcast_address(self, client: AsyncClient):
        """Test discovery with custom broadcast address."""
        # Test with specific network range
        broadcast_addr = "192.168.1.255"
        response = await client.get(f"/scan?broadcast_address={broadcast_addr}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should complete and return proper format
        assert "discovered_count" in data
        assert "devices" in data
        
        # All discovered devices should be in the specified network range
        for device in data["devices"]:
            assert device["ip"].startswith("192.168.1.")

    async def test_discovery_timeout_handling(self, client: AsyncClient):
        """Test discovery with custom timeout values."""
        # Test short timeout
        response = await client.get("/scan?timeout=2.0")
        assert response.status_code == status.HTTP_200_OK
        
        # Test longer timeout
        response = await client.get("/scan?timeout=10.0")
        assert response.status_code == status.HTTP_200_OK
        
        # Both should complete within reasonable time
        # (Implementation should handle timeouts properly)

    async def test_discovery_device_state_accuracy(self, client: AsyncClient):
        """Test that discovered devices have accurate state information."""
        response = await client.get("/scan")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        for device in data["devices"]:
            # Available devices should have current state
            if device["available"]:
                assert "state" in device  # power on/off
                
                # If device is on, may have brightness/color info
                if device["state"] and "brightness" in device:
                    assert 0 <= device["brightness"] <= 255
                    
                if "colortemp" in device:
                    assert 1000 <= device["colortemp"] <= 10000

    async def test_discovery_error_scenarios(self, client: AsyncClient):
        """Test discovery handles error scenarios gracefully."""
        # Test with invalid broadcast address
        response = await client.get("/scan?broadcast_address=invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test with invalid timeout
        response = await client.get("/scan?timeout=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test with timeout too high
        response = await client.get("/scan?timeout=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_discovery_concurrent_requests(self, client: AsyncClient):
        """Test that concurrent discovery requests are handled properly."""
        import asyncio
        
        # Launch multiple discovery requests concurrently
        tasks = [
            client.get("/scan"),
            client.get("/scan?timeout=3.0"),
            client.get("/scan?broadcast_address=255.255.255.255")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should complete successfully
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "scan_id" in data
            assert "discovered_count" in data

    async def test_discovery_pywizlight_integration(self, client: AsyncClient):
        """Test that discovery properly integrates with pywizlight library."""
        response = await client.get("/scan")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Should use pywizlight discovery mechanism
        # This test validates that the integration layer works
        for device in data["devices"]:
            # Device should have fields that come from pywizlight
            assert "ip" in device
            
            # If MAC address is available from pywizlight
            if "mac" in device:
                # Should be valid MAC format
                mac = device["mac"]
                assert len(mac.replace(":", "").replace("-", "")) == 12
                
    @pytest.mark.skip(reason="Requires real WiZ lights on network - use --real-lights to enable")
    async def test_discovery_with_real_lights(self, client: AsyncClient):
        """Test discovery with actual WiZ lights (requires --real-lights flag)."""
        response = await client.get("/scan")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # With real lights, should find at least one device
        assert data["discovered_count"] > 0
        assert len(data["devices"]) > 0
        
        # First device should have complete information
        first_device = data["devices"][0]
        assert first_device["available"] is True
        assert isinstance(first_device["state"], bool)
        
        # Should have additional metadata from real light
        assert "brightness" in first_device or "colortemp" in first_device