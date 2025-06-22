"""Tests for HTTP client."""

import json
from unittest.mock import Mock, patch, AsyncMock

import pytest
import httpx

from toyyibpay.http_client import HTTPClient, AsyncHTTPClient
from toyyibpay.config import ToyyibPayConfig
from toyyibpay.exceptions import (
    APIError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    AuthenticationError,
)


class TestHTTPClient:
    """Test synchronous HTTP client."""
    
    @pytest.mark.unit
    def test_http_client_initialization(self, test_config):
        """Test HTTP client initialization."""
        client = HTTPClient(test_config)
        
        assert client.config == test_config
        assert client._client is None  # Lazy initialization
    
    @pytest.mark.unit
    def test_http_client_lazy_initialization(self, test_config):
        """Test HTTP client lazy initialization."""
        http_client = HTTPClient(test_config)
        
        # Client should be created on first access
        client = http_client.client
        assert client is not None
        assert isinstance(client, httpx.Client)
        
        # Should reuse same client
        assert http_client.client is client
    
    @pytest.mark.unit
    def test_get_default_headers(self, test_config):
        """Test getting default headers."""
        http_client = HTTPClient(test_config)
        headers = http_client._get_default_headers()
        
        assert headers["User-Agent"] == "ToyyibPay-Python/0.1.0"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/x-www-form-urlencoded"
    
    @pytest.mark.unit
    def test_get_default_headers_with_additional(self):
        """Test getting default headers with additional headers."""
        config = ToyyibPayConfig(
            api_key="test-key",
            additional_headers={"X-Custom": "value", "X-Another": "header"}
        )
        http_client = HTTPClient(config)
        headers = http_client._get_default_headers()
        
        assert headers["X-Custom"] == "value"
        assert headers["X-Another"] == "header"
        assert headers["User-Agent"] == "ToyyibPay-Python/0.1.0"
    
    @pytest.mark.unit
    def test_prepare_data(self, test_config):
        """Test preparing request data."""
        http_client = HTTPClient(test_config)
        
        # Without additional data
        data = http_client._prepare_data()
        assert data == {"userSecretKey": test_config.api_key}
        
        # With additional data
        data = http_client._prepare_data({"billCode": "ABC123", "amount": 100})
        assert data == {
            "userSecretKey": test_config.api_key,
            "billCode": "ABC123",
            "amount": 100,
        }
    
    @pytest.mark.unit
    def test_handle_response_success(self, test_config):
        """Test handling successful response."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"success": True, "data": "test"}
        
        result = http_client._handle_response(mock_response)
        assert result == {"success": True, "data": "test"}
    
    @pytest.mark.unit
    def test_handle_response_array(self, test_config):
        """Test handling array response."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        
        result = http_client._handle_response(mock_response)
        assert result == {"data": [{"id": 1}, {"id": 2}]}
    
    @pytest.mark.unit
    def test_handle_response_plain_text(self, test_config):
        """Test handling plain text response."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_response.text = "Plain text response"
        
        result = http_client._handle_response(mock_response)
        assert result == {"response": "Plain text response"}
    
    @pytest.mark.unit
    def test_handle_http_error_401(self, test_config):
        """Test handling 401 authentication error."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}
        
        error = httpx.HTTPStatusError("401", request=Mock(), response=mock_response)
        
        with pytest.raises(AuthenticationError) as exc_info:
            http_client._handle_http_error(error)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.unit
    def test_handle_http_error_429(self, test_config):
        """Test handling 429 rate limit error."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        
        error = httpx.HTTPStatusError("429", request=Mock(), response=mock_response)
        
        with pytest.raises(RateLimitError) as exc_info:
            http_client._handle_http_error(error)
        
        assert exc_info.value.status_code == 429
    
    @pytest.mark.unit
    def test_handle_http_error_500(self, test_config):
        """Test handling 500 server error."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        
        error = httpx.HTTPStatusError("500", request=Mock(), response=mock_response)
        
        with pytest.raises(APIError) as exc_info:
            http_client._handle_http_error(error)
        
        assert "Server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500
    
    @pytest.mark.unit
    def test_handle_http_error_no_json(self, test_config):
        """Test handling HTTP error without JSON response."""
        http_client = HTTPClient(test_config)
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        
        error = httpx.HTTPStatusError("400 Bad Request", request=Mock(), response=mock_response)
        
        with pytest.raises(APIError) as exc_info:
            http_client._handle_http_error(error)
        
        assert "400 Bad Request" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_request_success(self, test_config, mock_httpx_client):
        """Test successful request."""
        http_client = HTTPClient(test_config)
        mock_client, mock_response = mock_httpx_client
        
        mock_response.json.return_value = {"success": True}
        
        result = http_client.request("POST", "createBill", data={"amount": 100})
        
        assert result == {"success": True}
        mock_client.request.assert_called_once()
        
        # Check request details
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "createBill" in call_args[1]["url"]
        assert call_args[1]["data"]["userSecretKey"] == test_config.api_key
        assert call_args[1]["data"]["amount"] == 100
    
    @pytest.mark.unit
    def test_request_timeout_error(self, test_config, mock_httpx_client):
        """Test request timeout error."""
        http_client = HTTPClient(test_config)
        mock_client, _ = mock_httpx_client
        
        mock_client.request.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(TimeoutError, match="Request timed out"):
            http_client.request("POST", "createBill")
    
    @pytest.mark.unit
    def test_request_network_error(self, test_config, mock_httpx_client):
        """Test request network error."""
        http_client = HTTPClient(test_config)
        mock_client, _ = mock_httpx_client
        
        mock_client.request.side_effect = httpx.NetworkError("Network error")
        
        with pytest.raises(NetworkError, match="Network error"):
            http_client.request("POST", "createBill")
    
    @pytest.mark.unit
    def test_get_method(self, test_config, mock_httpx_client):
        """Test GET method."""
        http_client = HTTPClient(test_config)
        mock_client, mock_response = mock_httpx_client
        
        mock_response.json.return_value = {"data": "test"}
        
        result = http_client.get("getCategories", params={"status": "active"})
        
        assert result == {"data": "test"}
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert call_args[1]["params"] == {"status": "active"}
    
    @pytest.mark.unit
    def test_post_method(self, test_config, mock_httpx_client):
        """Test POST method."""
        http_client = HTTPClient(test_config)
        mock_client, mock_response = mock_httpx_client
        
        mock_response.json.return_value = {"created": True}
        
        result = http_client.post("createBill", data={"amount": 100})
        
        assert result == {"created": True}
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["data"]["amount"] == 100
    
    @pytest.mark.unit
    def test_context_manager(self, test_config):
        """Test HTTP client as context manager."""
        with HTTPClient(test_config) as client:
            assert client._client is None  # Not yet initialized
        
        # After exit, should be closed
        assert client._client is None
    
    @pytest.mark.unit
    def test_close(self, test_config):
        """Test closing HTTP client."""
        http_client = HTTPClient(test_config)
        
        # Initialize client
        _ = http_client.client
        assert http_client._client is not None
        
        # Close
        http_client.close()
        assert http_client._client is None


@pytest.mark.asyncio
class TestAsyncHTTPClient:
    """Test asynchronous HTTP client."""
    
    @pytest.mark.asyncio
    async def test_async_http_client_context_manager(self, test_config):
        """Test async HTTP client as context manager."""
        async with AsyncHTTPClient(test_config) as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)
    
    @pytest.mark.asyncio
    async def test_async_request_success(self, test_config, mock_async_httpx_client):
        """Test successful async request."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"success": True}
        
        async with AsyncHTTPClient(test_config) as http_client:
            result = await http_client.request("POST", "createBill", data={"amount": 100})
            
            assert result == {"success": True}
    
    @pytest.mark.asyncio
    async def test_async_request_without_context_manager(self, test_config):
        """Test async request without context manager raises error."""
        http_client = AsyncHTTPClient(test_config)
        
        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await http_client.request("POST", "createBill")
    
    @pytest.mark.asyncio
    async def test_async_get_method(self, test_config, mock_async_httpx_client):
        """Test async GET method."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"data": "test"}
        
        async with AsyncHTTPClient(test_config) as http_client:
            result = await http_client.get("getCategories")
            assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_async_post_method(self, test_config, mock_async_httpx_client):
        """Test async POST method."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"created": True}
        
        async with AsyncHTTPClient(test_config) as http_client:
            result = await http_client.post("createBill", data={"amount": 100})
            assert result == {"created": True}
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self, test_config, mock_async_httpx_client):
        """Test async error handling."""
        mock_client, mock_response = mock_async_httpx_client
        
        # Simulate network error
        async def raise_network_error(*args, **kwargs):
            raise httpx.NetworkError("Connection failed")
        
        mock_client.request = raise_network_error
        
        async with AsyncHTTPClient(test_config) as http_client:
            with pytest.raises(NetworkError, match="Network error"):
                await http_client.request("POST", "createBill")