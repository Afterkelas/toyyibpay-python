"""HTTP client for ToyyibPay SDK."""

import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

import httpx
from httpx import Response, AsyncClient, Client

from .config import ToyyibPayConfig
from .exceptions import (
    APIError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    AuthenticationError,
)


class HTTPClient:
    """Synchronous HTTP client for ToyyibPay API."""

    def __init__(self, config: ToyyibPayConfig) -> None:
        self.config = config
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = Client(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers=self._get_default_headers(),
            )
        return self._client

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "User-Agent": "ToyyibPay-Python/0.1.1",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        headers.update(self.config.additional_headers)
        return headers

    def _prepare_data(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare request data with authentication."""
        request_data = {"userSecretKey": self.config.api_key}
        if data:
            request_data.update(data)
        return request_data

    def _handle_response(self, response: Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)

        try:
            # ToyyibPay sometimes returns array for certain endpoints
            response_data = response.json()
            if isinstance(response_data, list):
                return {"data": response_data}
            return response_data
        except json.JSONDecodeError:
            # Some endpoints return plain text
            return {"response": response.text}

    def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate exceptions."""
        status_code = error.response.status_code

        try:
            error_data = error.response.json()
            message = error_data.get("message", str(error))
        except (json.JSONDecodeError, AttributeError):
            message = str(error)
            error_data = None

        if status_code == 401:
            raise AuthenticationError(
                message="Invalid API key",
                status_code=status_code,
                response=error_data,
            )
        elif status_code == 429:
            raise RateLimitError(
                message="Rate limit exceeded",
                status_code=status_code,
                response=error_data,
            )
        elif status_code >= 500:
            raise APIError(
                message=f"Server error: {message}",
                status_code=status_code,
                response=error_data,
            )
        else:
            raise APIError(
                message=message,
                status_code=status_code,
                response=error_data,
            )

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to ToyyibPay API."""
        url = urljoin(self.config.api_base_url + "/", endpoint)
        prepared_data = self._prepare_data(data)

        try:
            response = self.client.request(
                method=method,
                url=url,
                data=prepared_data,
                params=params,
            )
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request."""
        return self.request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self.request("POST", endpoint, data=data)

    def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "HTTPClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client for ToyyibPay API."""

    def __init__(self, config: ToyyibPayConfig) -> None:
        self.config = config
        self._client: Optional[AsyncClient] = None

    async def __aenter__(self) -> "AsyncHTTPClient":
        """Enter async context manager."""
        self._client = AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers=self._get_default_headers(),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {
            "User-Agent": "ToyyibPay-Python/0.1.1",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        headers.update(self.config.additional_headers)
        return headers

    def _prepare_data(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare request data with authentication."""
        request_data = {"userSecretKey": self.config.api_key}
        if data:
            request_data.update(data)
        return request_data

    async def _handle_response(self, response: Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e)

        try:
            response_data = response.json()
            if isinstance(response_data, list):
                return {"data": response_data}
            return response_data
        except json.JSONDecodeError:
            return {"response": response.text}

    async def _handle_http_error(self, error: httpx.HTTPStatusError) -> None:
        """Handle HTTP errors and raise appropriate exceptions."""
        status_code = error.response.status_code

        try:
            error_data = error.response.json()
            message = error_data.get("message", str(error))
        except (json.JSONDecodeError, AttributeError):
            message = str(error)
            error_data = None

        if status_code == 401:
            raise AuthenticationError(
                message="Invalid API key",
                status_code=status_code,
                response=error_data,
            )
        elif status_code == 429:
            raise RateLimitError(
                message="Rate limit exceeded",
                status_code=status_code,
                response=error_data,
            )
        elif status_code >= 500:
            raise APIError(
                message=f"Server error: {message}",
                status_code=status_code,
                response=error_data,
            )
        else:
            raise APIError(
                message=message,
                status_code=status_code,
                response=error_data,
            )

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make async HTTP request to ToyyibPay API."""
        if not self._client:
            raise RuntimeError(
                "AsyncHTTPClient must be used as async context manager")

        url = urljoin(self.config.api_base_url + "/", endpoint)
        prepared_data = self._prepare_data(data)

        try:
            response = await self._client.request(
                method=method,
                url=url,
                data=prepared_data,
                params=params,
            )
            return await self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timed out: {e}")
        except httpx.NetworkError as e:
            raise NetworkError(f"Network error: {e}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make async GET request."""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make async POST request."""
        return await self.request("POST", endpoint, data=data)
