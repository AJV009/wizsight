"""
Contract test for POST /lights/{ip}/brightness endpoint.

This test validates the API contract against the OpenAPI specification.
It MUST FAIL until the endpoint is implemented.
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


class TestLightsBrightnessContract:
    """Contract tests for POST /lights/{ip}/brightness endpoint per OpenAPI specification."""

    async def test_brightness_endpoint_exists(self, client: AsyncClient):
        """Test that /lights/{ip}/brightness endpoint exists and accepts POST requests."""
        payload = {"brightness": 150}
        response = await client.post("/lights/192.168.1.100/brightness", json=payload)
        
        # Should not return 404 or 405 (endpoint exists and accepts POST)
        assert response.status_code not in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_brightness_valid_request(self, client: AsyncClient):
        """Test brightness control with valid parameters."""
        test_ip = "192.168.1.100"
        payload = {"brightness": 200, "force_on": True}
        response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
        
        # Should return 200 OK for successful operation (or 400 if light unreachable)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"

    async def test_brightness_required_field(self, client: AsyncClient):
        """Test that brightness field is required."""
        test_ip = "192.168.1.100"
        payload = {"force_on": True}  # Missing required brightness
        response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
        
        # Should return 422 for missing required field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_brightness_range_validation(self, client: AsyncClient):
        """Test brightness value range validation (0-255)."""
        test_ip = "192.168.1.100"
        
        # Test invalid values
        invalid_values = [-1, 256, 999, -100]
        for brightness in invalid_values:
            payload = {"brightness": brightness}
            response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
            
            # Should return 422 for out-of-range values
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_brightness_valid_range(self, client: AsyncClient):
        """Test brightness with valid range values."""
        test_ip = "192.168.1.100"
        
        # Test valid boundary values
        valid_values = [0, 1, 128, 254, 255]
        for brightness in valid_values:
            payload = {"brightness": brightness}
            response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
            
            # Should not fail due to validation
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_brightness_force_on_default(self, client: AsyncClient):
        """Test that force_on defaults to true if not provided."""
        test_ip = "192.168.1.100"
        payload = {"brightness": 150}  # No force_on specified
        response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
        
        # Should accept the request (defaults applied)
        assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_brightness_force_on_boolean(self, client: AsyncClient):
        """Test that force_on accepts boolean values."""
        test_ip = "192.168.1.100"
        
        for force_on_value in [True, False]:
            payload = {"brightness": 150, "force_on": force_on_value}
            response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
            
            # Should accept boolean values
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_brightness_response_schema(self, client: AsyncClient):
        """Test successful brightness response matches ControlResponse schema."""
        test_ip = "192.168.1.100"
        payload = {"brightness": 150}
        response = await client.post(f"/lights/{test_ip}/brightness", json=payload)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Required fields per ControlResponse schema
            assert "success" in data
            assert "target_ip" in data
            assert "response_time_ms" in data
            
            # Validate field types
            assert isinstance(data["success"], bool)
            assert data["target_ip"] == test_ip
            assert isinstance(data["response_time_ms"], (int, float))

    async def test_brightness_invalid_ip_format(self, client: AsyncClient):
        """Test brightness endpoint with invalid IP format."""
        payload = {"brightness": 150}
        invalid_ip = "invalid-ip"
        response = await client.post(f"/lights/{invalid_ip}/brightness", json=payload)
        
        # Should return validation error
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_brightness_no_body(self, client: AsyncClient):
        """Test brightness endpoint without request body."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/brightness")
        
        # Should return 422 for missing request body
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY