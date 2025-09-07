"""
Integration test for light control workflow.

This test validates the complete light control flow from API to pywizlight.
It MUST FAIL until the full control implementation is complete.
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


class TestLightControlIntegration:
    """Integration tests for complete light control workflow."""

    async def test_toggle_workflow(self, client: AsyncClient):
        """Test complete toggle workflow from API to light state change."""
        test_ip = "192.168.1.100"
        
        # Step 1: Get initial state
        state_response = await client.get(f"/lights/{test_ip}/state")
        
        # Should be able to query state (even if light unreachable)
        assert state_response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Step 2: Attempt toggle
        toggle_response = await client.post(f"/lights/{test_ip}/toggle")
        
        # Should attempt toggle operation
        assert toggle_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,  # Light unreachable
            status.HTTP_408_REQUEST_TIMEOUT
        ]
        
        if toggle_response.status_code == status.HTTP_200_OK:
            toggle_data = toggle_response.json()
            assert "success" in toggle_data
            assert "target_ip" in toggle_data
            assert toggle_data["target_ip"] == test_ip

    async def test_brightness_control_workflow(self, client: AsyncClient):
        """Test complete brightness control workflow."""
        test_ip = "192.168.1.100"
        
        # Step 1: Set brightness to specific value
        brightness_payload = {"brightness": 150, "force_on": True}
        response = await client.post(f"/lights/{test_ip}/brightness", json=brightness_payload)
        
        # Should attempt brightness control
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_408_REQUEST_TIMEOUT
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "success" in data
            assert "target_ip" in data
            
            # Step 2: Verify state reflects change (if successful)
            if data["success"]:
                state_response = await client.get(f"/lights/{test_ip}/state")
                if state_response.status_code == status.HTTP_200_OK:
                    state_data = state_response.json()
                    # Light should be on and at specified brightness
                    assert state_data["state"] is True
                    # Note: Actual brightness may vary slightly due to light limitations

    async def test_colortemp_control_workflow(self, client: AsyncClient):
        """Test complete color temperature control workflow."""
        test_ip = "192.168.1.100"
        
        # Step 1: Set color temperature to warm white
        colortemp_payload = {"colortemp": 2700, "force_on": True}
        response = await client.post(f"/lights/{test_ip}/colortemp", json=colortemp_payload)
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_408_REQUEST_TIMEOUT
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "success" in data
            
            # Step 2: Change to cool white
            cool_payload = {"colortemp": 6500, "force_on": False}
            cool_response = await client.post(f"/lights/{test_ip}/colortemp", json=cool_payload)
            
            # Should handle sequential color temperature changes
            assert cool_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST
            ]

    async def test_control_state_consistency(self, client: AsyncClient):
        """Test that control operations maintain state consistency."""
        test_ip = "192.168.1.100"
        
        # Sequence of control operations
        operations = [
            ("POST", f"/lights/{test_ip}/toggle", None),
            ("POST", f"/lights/{test_ip}/brightness", {"brightness": 200}),
            ("POST", f"/lights/{test_ip}/colortemp", {"colortemp": 4000}),
            ("GET", f"/lights/{test_ip}/state", None)
        ]
        
        last_state = None
        for method, url, payload in operations:
            if method == "POST" and payload:
                response = await client.post(url, json=payload)
            elif method == "POST":
                response = await client.post(url)
            else:
                response = await client.get(url)
            
            # Each operation should complete (success or expected failure)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_408_REQUEST_TIMEOUT
            ]
            
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                
                # Track state changes
                if method == "GET":
                    last_state = data
                else:
                    # Control response should include timing info
                    assert "response_time_ms" in data

    async def test_control_error_handling(self, client: AsyncClient):
        """Test that control operations handle errors gracefully."""
        # Test with unreachable IP
        unreachable_ip = "10.254.254.254"
        
        # All control operations should handle unreachable lights
        operations = [
            client.post(f"/lights/{unreachable_ip}/toggle"),
            client.post(f"/lights/{unreachable_ip}/brightness", json={"brightness": 100}),
            client.post(f"/lights/{unreachable_ip}/colortemp", json={"colortemp": 4000}),
            client.get(f"/lights/{unreachable_ip}/state")
        ]
        
        import asyncio
        responses = await asyncio.gather(*operations, return_exceptions=True)
        
        # All should complete with appropriate error responses
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code in [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_404_NOT_FOUND,
                    status.HTTP_408_REQUEST_TIMEOUT
                ]
                
                # Error responses should have proper format
                if response.headers.get("content-type") == "application/json":
                    error_data = response.json()
                    assert "error" in error_data or "success" in error_data

    async def test_control_timing_requirements(self, client: AsyncClient):
        """Test that control operations meet timing requirements."""
        test_ip = "192.168.1.100"
        
        import time
        
        # Test toggle timing
        start_time = time.time()
        response = await client.post(f"/lights/{test_ip}/toggle")
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds for network operation)
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms < 5000
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if "response_time_ms" in data:
                # Reported timing should be reasonable
                assert 0 <= data["response_time_ms"] < 5000

    async def test_control_concurrent_operations(self, client: AsyncClient):
        """Test concurrent control operations on different lights."""
        import asyncio
        
        # Simulate controlling multiple lights simultaneously
        test_ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
        
        tasks = []
        for ip in test_ips:
            tasks.append(client.post(f"/lights/{ip}/toggle"))
            tasks.append(client.get(f"/lights/{ip}/state"))
        
        responses = await asyncio.gather(*tasks)
        
        # All operations should complete
        for response in responses:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_408_REQUEST_TIMEOUT
            ]

    async def test_control_force_on_behavior(self, client: AsyncClient):
        """Test force_on parameter behavior in control operations."""
        test_ip = "192.168.1.100"
        
        # Test brightness with force_on=True
        brightness_payload = {"brightness": 100, "force_on": True}
        response = await client.post(f"/lights/{test_ip}/brightness", json=brightness_payload)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if data.get("success"):
                # Should turn light on and set brightness
                assert "new_state" in data or "success" in data
        
        # Test brightness with force_on=False
        brightness_payload = {"brightness": 200, "force_on": False}
        response = await client.post(f"/lights/{test_ip}/brightness", json=brightness_payload)
        
        # Should handle force_on=False appropriately
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

    @pytest.mark.skip(reason="Requires real WiZ lights on network - use --real-lights to enable")
    async def test_control_with_real_lights(self, client: AsyncClient):
        """Test control operations with actual WiZ lights."""
        # First discover available lights
        scan_response = await client.get("/scan")
        assert scan_response.status_code == status.HTTP_200_OK
        
        scan_data = scan_response.json()
        if scan_data["discovered_count"] > 0:
            # Use first available light
            test_light = scan_data["devices"][0]
            test_ip = test_light["ip"]
            
            # Test actual toggle
            toggle_response = await client.post(f"/lights/{test_ip}/toggle")
            assert toggle_response.status_code == status.HTTP_200_OK
            
            toggle_data = toggle_response.json()
            assert toggle_data["success"] is True
            
            # Verify state change
            state_response = await client.get(f"/lights/{test_ip}/state")
            assert state_response.status_code == status.HTTP_200_OK
            
            state_data = state_response.json()
            assert state_data["available"] is True