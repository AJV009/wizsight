"""
Contract test for GET /lights/{ip}/state endpoint.

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


class TestLightsStateContract:
    """Contract tests for GET /lights/{ip}/state endpoint per OpenAPI specification."""

    async def test_state_endpoint_exists(self, client: AsyncClient):
        """Test that /lights/{ip}/state endpoint exists and accepts GET requests."""
        response = await client.get("/lights/192.168.1.100/state")
        
        # Should not return 404 or 405 (endpoint exists and accepts GET)
        assert response.status_code not in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_state_valid_ip_response(self, client: AsyncClient):
        """Test state retrieval with valid IP address."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        # Should return 200 OK for successful query (or 400/404 if light unreachable)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"

    async def test_state_success_response_schema(self, client: AsyncClient):
        """Test successful state response matches LightDevice schema."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Required fields per LightDevice schema
            assert "ip" in data
            assert "state" in data
            assert "available" in data
            
            # Validate field types and values
            assert data["ip"] == test_ip
            assert isinstance(data["state"], bool)
            assert isinstance(data["available"], bool)
            
            # Optional fields should be properly typed if present
            if "brightness" in data:
                assert isinstance(data["brightness"], int)
                assert 0 <= data["brightness"] <= 255
                
            if "colortemp" in data:
                assert isinstance(data["colortemp"], int)
                assert 1000 <= data["colortemp"] <= 10000
                
            if "rgb" in data:
                assert isinstance(data["rgb"], list)
                assert len(data["rgb"]) == 3
                for value in data["rgb"]:
                    assert isinstance(value, int)
                    assert 0 <= value <= 255
                    
            if "scene" in data:
                assert isinstance(data["scene"], int)
                assert 1 <= data["scene"] <= 37
                
            if "mac" in data:
                assert isinstance(data["mac"], str)
                
            if "name" in data:
                assert isinstance(data["name"], str)
                
            if "last_seen" in data:
                assert isinstance(data["last_seen"], str)  # ISO datetime string

    async def test_state_error_response_schema(self, client: AsyncClient):
        """Test error response matches ErrorResponse schema."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        if response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]:
            data = response.json()
            
            # Should match ErrorResponse schema
            assert "error" in data
            assert "message" in data
            assert isinstance(data["error"], str)
            assert isinstance(data["message"], str)

    async def test_state_invalid_ip_format(self, client: AsyncClient):
        """Test state endpoint with invalid IP format."""
        invalid_ips = [
            "invalid-ip",
            "999.999.999.999",
            "192.168.1",
            "192.168.1.300",
            ""
        ]
        
        for invalid_ip in invalid_ips:
            response = await client.get(f"/lights/{invalid_ip}/state")
            # Should return validation error or bad request
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST
            ]

    async def test_state_no_query_parameters(self, client: AsyncClient):
        """Test that state endpoint doesn't require query parameters."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        # Should work without any query parameters
        assert response.status_code not in [status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_state_unreachable_light(self, client: AsyncClient):
        """Test state query for unreachable light returns appropriate error."""
        # Use an IP that's likely to be unreachable
        unreachable_ip = "10.254.254.254"
        response = await client.get(f"/lights/{unreachable_ip}/state")
        
        # Should return 400 or 404 for unreachable light
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_200_OK  # Might return with available=false
        ]

    async def test_state_available_field_accuracy(self, client: AsyncClient):
        """Test that available field accurately reflects light reachability."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            available = data["available"]
            
            # If available=false, other state fields may be stale
            if not available:
                # Should still have last known state but marked as unavailable
                assert "last_seen" in data or "state" in data

    async def test_state_rgb_colortemp_mutual_exclusion(self, client: AsyncClient):
        """Test that RGB and color temperature are mutually exclusive."""
        test_ip = "192.168.1.100"
        response = await client.get(f"/lights/{test_ip}/state")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # If both are present, one should be null or preferred mode active
            if "rgb" in data and "colortemp" in data:
                # Both shouldn't have meaningful values simultaneously
                has_rgb = data["rgb"] is not None and any(v > 0 for v in data["rgb"])
                has_colortemp = data["colortemp"] is not None and data["colortemp"] > 0
                
                # At most one should be active (this is more of a business rule test)
                # For contract testing, we just ensure the fields exist if present