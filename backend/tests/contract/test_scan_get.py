"""
Contract test for GET /scan endpoint.

This test validates the API contract against the OpenAPI specification.
It MUST FAIL until the endpoint is implemented.
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.fixture
async def client():
    """Create test client for the FastAPI application."""
    from src.api.main import app
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestScanGetContract:
    """Contract tests for GET /scan endpoint per OpenAPI specification."""

    async def test_scan_endpoint_exists(self, client: AsyncClient):
        """Test that /scan endpoint exists and accepts GET requests."""
        response = await client.get("/scan")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != status.HTTP_404_NOT_FOUND
        
    async def test_scan_default_parameters(self, client: AsyncClient):
        """Test /scan with default parameters returns valid response."""
        response = await client.get("/scan")
        
        # Should return 200 OK for successful scan
        assert response.status_code == status.HTTP_200_OK
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"
        
        # Response should match ScanResponse schema
        data = response.json()
        assert "scan_id" in data
        assert "status" in data
        assert "discovered_count" in data
        assert "devices" in data
        
        # Validate field types per OpenAPI spec
        assert isinstance(data["scan_id"], str)
        assert data["status"] in ["in_progress", "completed", "failed"]
        assert isinstance(data["discovered_count"], int)
        assert isinstance(data["devices"], list)
        assert data["discovered_count"] >= 0

    async def test_scan_with_custom_broadcast_address(self, client: AsyncClient):
        """Test /scan with custom broadcast_address parameter."""
        response = await client.get("/scan?broadcast_address=192.168.1.255")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "scan_id" in data
        assert "status" in data

    async def test_scan_with_custom_timeout(self, client: AsyncClient):
        """Test /scan with custom timeout parameter."""
        response = await client.get("/scan?timeout=10.0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "scan_id" in data
        
    async def test_scan_with_invalid_timeout_low(self, client: AsyncClient):
        """Test /scan with timeout below minimum (1.0) returns validation error."""
        response = await client.get("/scan?timeout=0.5")
        
        # Should return 422 for validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_scan_with_invalid_timeout_high(self, client: AsyncClient):
        """Test /scan with timeout above maximum (30.0) returns validation error."""
        response = await client.get("/scan?timeout=35.0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_scan_with_invalid_broadcast_address(self, client: AsyncClient):
        """Test /scan with invalid IPv4 broadcast address returns validation error."""
        response = await client.get("/scan?broadcast_address=invalid-ip")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_scan_error_response_format(self, client: AsyncClient):
        """Test that error responses match ErrorResponse schema."""
        # This will be tested when we have actual error conditions
        # For now, just ensure 500 errors have proper format
        pass

    async def test_scan_device_fields(self, client: AsyncClient):
        """Test that discovered devices have required LightDevice fields."""
        response = await client.get("/scan")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if data["discovered_count"] > 0:
                device = data["devices"][0]
                
                # Required fields per LightDevice schema
                assert "ip" in device
                assert "state" in device
                assert "available" in device
                
                # Validate field types
                assert isinstance(device["ip"], str)
                assert isinstance(device["state"], bool)
                assert isinstance(device["available"], bool)
                
                # Optional fields should be properly typed if present
                if "brightness" in device:
                    assert isinstance(device["brightness"], int)
                    assert 0 <= device["brightness"] <= 255
                    
                if "colortemp" in device:
                    assert isinstance(device["colortemp"], int)
                    assert 1000 <= device["colortemp"] <= 10000