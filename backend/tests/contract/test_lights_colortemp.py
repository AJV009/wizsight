"""
Contract test for POST /lights/{ip}/colortemp endpoint.

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


class TestLightsColortempContract:
    """Contract tests for POST /lights/{ip}/colortemp endpoint per OpenAPI specification."""

    async def test_colortemp_endpoint_exists(self, client: AsyncClient):
        """Test that /lights/{ip}/colortemp endpoint exists and accepts POST requests."""
        payload = {"colortemp": 4000}
        response = await client.post("/lights/192.168.1.100/colortemp", json=payload)
        
        # Should not return 404 or 405 (endpoint exists and accepts POST)
        assert response.status_code not in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_colortemp_valid_request(self, client: AsyncClient):
        """Test color temperature control with valid parameters."""
        test_ip = "192.168.1.100"
        payload = {"colortemp": 5000, "force_on": True}
        response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
        
        # Should return 200 OK for successful operation (or 400 if light unreachable)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"

    async def test_colortemp_required_field(self, client: AsyncClient):
        """Test that colortemp field is required."""
        test_ip = "192.168.1.100"
        payload = {"force_on": True}  # Missing required colortemp
        response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
        
        # Should return 422 for missing required field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_colortemp_range_validation(self, client: AsyncClient):
        """Test color temperature value range validation (1000-10000K)."""
        test_ip = "192.168.1.100"
        
        # Test invalid values
        invalid_values = [999, 10001, 500, 15000, -1000]
        for colortemp in invalid_values:
            payload = {"colortemp": colortemp}
            response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
            
            # Should return 422 for out-of-range values
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_colortemp_valid_range(self, client: AsyncClient):
        """Test color temperature with valid range values."""
        test_ip = "192.168.1.100"
        
        # Test valid values (warm to cool)
        valid_values = [1000, 2700, 4000, 5500, 6500, 10000]
        for colortemp in valid_values:
            payload = {"colortemp": colortemp}
            response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
            
            # Should not fail due to validation
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_colortemp_force_on_default(self, client: AsyncClient):
        """Test that force_on defaults to true if not provided."""
        test_ip = "192.168.1.100"
        payload = {"colortemp": 4000}  # No force_on specified
        response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
        
        # Should accept the request (defaults applied)
        assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_colortemp_force_on_boolean(self, client: AsyncClient):
        """Test that force_on accepts boolean values."""
        test_ip = "192.168.1.100"
        
        for force_on_value in [True, False]:
            payload = {"colortemp": 4000, "force_on": force_on_value}
            response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
            
            # Should accept boolean values
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_colortemp_response_schema(self, client: AsyncClient):
        """Test successful colortemp response matches ControlResponse schema."""
        test_ip = "192.168.1.100"
        payload = {"colortemp": 4000}
        response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
        
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

    async def test_colortemp_warm_white_range(self, client: AsyncClient):
        """Test warm white color temperatures (2700K-3000K)."""
        test_ip = "192.168.1.100"
        warm_temps = [2700, 2800, 3000]
        
        for temp in warm_temps:
            payload = {"colortemp": temp}
            response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
            
            # Should accept warm white range
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_colortemp_cool_white_range(self, client: AsyncClient):
        """Test cool white color temperatures (5000K-6500K)."""
        test_ip = "192.168.1.100"
        cool_temps = [5000, 5500, 6000, 6500]
        
        for temp in cool_temps:
            payload = {"colortemp": temp}
            response = await client.post(f"/lights/{test_ip}/colortemp", json=payload)
            
            # Should accept cool white range
            assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_colortemp_invalid_ip_format(self, client: AsyncClient):
        """Test colortemp endpoint with invalid IP format."""
        payload = {"colortemp": 4000}
        invalid_ip = "invalid-ip"
        response = await client.post(f"/lights/{invalid_ip}/colortemp", json=payload)
        
        # Should return validation error
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_colortemp_no_body(self, client: AsyncClient):
        """Test colortemp endpoint without request body."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/colortemp")
        
        # Should return 422 for missing request body
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY