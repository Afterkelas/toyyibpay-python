"""Tests for ToyyibPay client."""

from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

import pytest
import httpx

import toyyibpay
from toyyibpay.exceptions import (
    ValidationError,
    AuthenticationError,
    APIError,
    NetworkError,
    TimeoutError,
)
from toyyibpay.enums import PaymentStatus, CORPORATE_BANKING_THRESHOLD


class TestToyyibPayClient:
    """Test ToyyibPay client functionality."""
    
    @pytest.mark.unit
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = toyyibpay.Client(api_key="test-key")
        assert client.config.api_key == "test-key"
        assert client.config.environment == "production"
    
    @pytest.mark.unit
    def test_client_initialization_with_config(self, test_config):
        """Test client initialization with config object."""
        client = toyyibpay.Client(config=test_config)
        assert client.config == test_config
    
    @pytest.mark.unit
    def test_client_initialization_from_global_config(self, test_config):
        """Test client initialization from global config."""
        toyyibpay.set_config(test_config)
        client = toyyibpay.Client()
        assert client.config == test_config
    
    @pytest.mark.unit
    def test_client_initialization_without_config(self):
        """Test client initialization without config raises error."""
        with pytest.raises(RuntimeError, match="configuration not set"):
            toyyibpay.Client()
    
    @pytest.mark.unit
    def test_create_bill_success(self, client, sample_bill_data, mock_httpx_client):
        """Test successful bill creation."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        bill = client.create_bill(**sample_bill_data)
        
        assert bill.bill_code == "ABC123"
        assert bill.payment_url == f"{client.config.base_url}/ABC123"
        
        # Verify request was made correctly
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "createBill" in call_args[1]["url"]
    
    @pytest.mark.unit
    def test_create_bill_with_decimal_amount(self, client, sample_bill_data, mock_httpx_client):
        """Test bill creation with Decimal amount."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        sample_bill_data["amount"] = Decimal("99.99")
        bill = client.create_bill(**sample_bill_data)
        
        assert bill.bill_code == "ABC123"
    
    @pytest.mark.unit
    def test_create_bill_validation_error(self, client, sample_bill_data):
        """Test bill creation with invalid amount."""
        sample_bill_data["amount"] = -10.00
        
        with pytest.raises(ValidationError, match="Amount must be greater than 0"):
            client.create_bill(**sample_bill_data)
    
    @pytest.mark.unit
    def test_create_bill_corporate_banking(self, client, sample_bill_data, mock_httpx_client):
        """Test bill creation enables corporate banking for large amounts."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        # Set amount above threshold
        sample_bill_data["amount"] = CORPORATE_BANKING_THRESHOLD + 1000
        
        bill = client.create_bill(**sample_bill_data)
        
        # Check that enableFPXB2B was set to 1 in the request
        call_args = mock_client.request.call_args
        request_data = call_args[1]["data"]
        assert request_data.get("enableFPXB2B") == 1
    
    @pytest.mark.unit
    def test_create_bill_api_error(self, client, sample_bill_data, mock_httpx_client):
        """Test bill creation with API error response."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"error": "Invalid request"}
        
        with pytest.raises(ValidationError, match="Failed to create bill"):
            client.create_bill(**sample_bill_data)
    
    @pytest.mark.unit
    def test_create_bill_from_input(self, client, mock_httpx_client):
        """Test bill creation from InitPaymentInput model."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        payment_input = toyyibpay.InitPaymentInput(
            order_id="ORD-12345",
            name="John Doe",
            email="john@example.com",
            phone="0123456789",
            amount=Decimal("100.00"),
        )
        
        bill = client.create_bill_from_input(payment_input)
        assert bill.bill_code == "ABC123"
    
    @pytest.mark.unit
    def test_get_bill_transactions_success(self, client, mock_httpx_client, sample_transaction_data):
        """Test getting bill transactions."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = [sample_transaction_data]
        
        transactions = client.get_bill_transactions("ABC123")
        
        assert len(transactions) == 1
        assert transactions[0].bill_to == "John Doe"
        assert transactions[0].bill_payment_status == PaymentStatus.SUCCESS
        
        # Verify request
        call_args = mock_client.request.call_args
        assert call_args[1]["data"]["billCode"] == "ABC123"
    
    @pytest.mark.unit
    def test_get_bill_transactions_with_status_filter(self, client, mock_httpx_client):
        """Test getting bill transactions with status filter."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = []
        
        transactions = client.get_bill_transactions(
            "ABC123",
            status=PaymentStatus.SUCCESS
        )
        
        # Verify status was included in request
        call_args = mock_client.request.call_args
        assert call_args[1]["data"]["billpaymentStatus"] == 1
    
    @pytest.mark.unit
    def test_get_bill_transactions_handles_dict_response(self, client, mock_httpx_client, sample_transaction_data):
        """Test getting bill transactions handles dict response."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"data": [sample_transaction_data]}
        
        transactions = client.get_bill_transactions("ABC123")
        assert len(transactions) == 1
    
    @pytest.mark.unit
    def test_check_payment_status_success(self, client, mock_httpx_client, sample_transaction_data):
        """Test checking payment status returns success."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = [sample_transaction_data]
        
        status = client.check_payment_status("ABC123")
        assert status == PaymentStatus.SUCCESS
    
    @pytest.mark.unit
    def test_check_payment_status_no_transactions(self, client, mock_httpx_client):
        """Test checking payment status with no transactions."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = []
        
        status = client.check_payment_status("ABC123")
        assert status is None
    
    @pytest.mark.unit
    def test_check_payment_status_failed(self, client, mock_httpx_client, sample_transaction_data):
        """Test checking payment status returns failed."""
        mock_client, mock_response = mock_httpx_client
        
        # First call returns empty (no successful transactions)
        mock_response.json.side_effect = [
            [],  # No successful transactions
            [{**sample_transaction_data, "billpaymentStatus": "3"}]  # Failed transaction
        ]
        
        status = client.check_payment_status("ABC123")
        assert status == PaymentStatus.FAILED
    
    @pytest.mark.unit
    def test_create_category_success(self, client, mock_httpx_client):
        """Test creating a category."""
        mock_client, mock_response = mock_httpx_client
        mock_response.json.return_value = {"CategoryCode": "CAT123"}
        
        result = client.create_category(
            name="Test Category",
            description="Test Description"
        )
        
        assert result["CategoryCode"] == "CAT123"
        
        # Verify request
        call_args = mock_client.request.call_args
        assert call_args[1]["data"]["catname"] == "Test Category"
        assert call_args[1]["data"]["catdescription"] == "Test Description"
    
    @pytest.mark.unit
    def test_context_manager(self, test_config):
        """Test client as context manager."""
        with toyyibpay.Client(config=test_config) as client:
            assert client.config == test_config
        
        # Verify cleanup was called
        assert client._http_client._client is None
    
    @pytest.mark.unit
    def test_http_error_handling(self, client, sample_bill_data, mock_httpx_client):
        """Test HTTP error handling."""
        mock_client, mock_response = mock_httpx_client
        
        # Simulate 401 error
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=Mock(),
            response=mock_response
        )
        mock_response.json.return_value = {"message": "Invalid API key"}
        
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            client.create_bill(**sample_bill_data)
    
    @pytest.mark.unit
    def test_network_error_handling(self, client, sample_bill_data, mock_httpx_client):
        """Test network error handling."""
        mock_client, mock_response = mock_httpx_client
        mock_client.request.side_effect = httpx.NetworkError("Connection failed")
        
        with pytest.raises(NetworkError, match="Network error"):
            client.create_bill(**sample_bill_data)
    
    @pytest.mark.unit
    def test_timeout_error_handling(self, client, sample_bill_data, mock_httpx_client):
        """Test timeout error handling."""
        mock_client, mock_response = mock_httpx_client
        mock_client.request.side_effect = httpx.TimeoutException("Request timed out")
        
        with pytest.raises(TimeoutError, match="Request timed out"):
            client.create_bill(**sample_bill_data)


class TestClientHelpers:
    """Test client helper functions."""
    
    @pytest.mark.unit
    def test_client_convenience_function(self):
        """Test Client() convenience function."""
        client = toyyibpay.Client(api_key="test-key")
        assert isinstance(client, toyyibpay.ToyyibPayClient)
        assert client.config.api_key == "test-key"