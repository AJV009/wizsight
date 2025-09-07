"""
Contract test for POST /lights/{ip}/toggle endpoint.

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


class TestLightsToggleContract:
    """Contract tests for POST /lights/{ip}/toggle endpoint per OpenAPI specification."""

    async def test_toggle_endpoint_exists(self, client: AsyncClient):
        """Test that /lights/{ip}/toggle endpoint exists and accepts POST requests."""
        response = await client.post("/lights/192.168.1.100/toggle")
        
        # Should not return 404 or 405 (endpoint exists and accepts POST)
        assert response.status_code not in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_toggle_valid_ip_success(self, client: AsyncClient):
        """Test /lights/{ip}/toggle with valid IP returns success response."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        # Should return 200 OK for successful toggle (or 400 if light unreachable)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST  # Light may be unreachable in test
        ]
        
        # Response should be JSON
        assert response.headers["content-type"] == "application/json"

    async def test_toggle_success_response_schema(self, client: AsyncClient):
        """Test successful toggle response matches ControlResponse schema."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            
            # Required fields per ControlResponse schema
            assert "success" in data
            assert "target_ip" in data
            assert "response_time_ms" in data
            
            # Validate field types and values
            assert isinstance(data["success"], bool)
            assert data["target_ip"] == test_ip
            assert isinstance(data["response_time_ms"], (int, float))
            assert data["response_time_ms"] >= 0
            
            # If successful, should have state information
            if data["success"]:
                assert "new_state" in data
                assert isinstance(data["new_state"], dict)

    async def test_toggle_error_response_schema(self, client: AsyncClient):
        """Test error response matches ErrorResponse schema."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            data = response.json()
            
            # Should match ControlResponse with error info
            assert "success" in data
            assert data["success"] is False
            assert "error_code" in data
            assert "error_message" in data
            assert "target_ip" in data
            assert data["target_ip"] == test_ip

    async def test_toggle_invalid_ip_format(self, client: AsyncClient):
        """Test /lights/{ip}/toggle with invalid IP format returns validation error."""
        invalid_ips = [
            "invalid-ip",
            "999.999.999.999", 
            "192.168.1",
            "192.168.1.300",
            ""
        ]
        
        for invalid_ip in invalid_ips:
            response = await client.post(f"/lights/{invalid_ip}/toggle")
            # Should return 422 for path parameter validation error
            # Or 400 for malformed IP handling
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST
            ]

    async def test_toggle_no_request_body_required(self, client: AsyncClient):
        """Test that toggle endpoint works without request body."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        # Should not fail due to missing request body
        assert response.status_code not in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ] or "body" not in response.text.lower()

    async def test_toggle_timeout_handling(self, client: AsyncClient):
        """Test that timeout scenarios return appropriate error code."""
        # Use an IP that's likely to timeout (non-routable)
        timeout_ip = "10.254.254.254"
        response = await client.post(f"/lights/{timeout_ip}/toggle")
        
        # Should return 408 for timeout or 400 for unreachable
        assert response.status_code in [
            status.HTTP_408_REQUEST_TIMEOUT,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_200_OK  # Might complete with error in response
        ]

    async def test_toggle_response_time_tracking(self, client: AsyncClient):
        """Test that response includes timing information."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]:
            data = response.json()
            assert "response_time_ms" in data
            # Response time should be reasonable (under 10 seconds)
            assert 0 <= data["response_time_ms"] <= 10000

    async def test_toggle_previous_state_capture(self, client: AsyncClient):
        """Test that successful toggle captures previous state."""
        test_ip = "192.168.1.100"
        response = await client.post(f"/lights/{test_ip}/toggle")
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            if data["success"]:
                # Should capture state before and after toggle
                assert "previous_state" in data or "new_state" in data
                
                if "previous_state" in data:
                    prev_state = data["previous_state"]
                    assert "state" in prev_state
                    assert isinstance(prev_state["state"], bool)