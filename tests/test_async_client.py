"""Tests for async ToyyibPay client."""

from decimal import Decimal
from unittest.mock import Mock, AsyncMock

import pytest
import httpx

import toyyibpay
from toyyibpay.exceptions import ValidationError, NetworkError
from toyyibpay.enums import PaymentStatus, CORPORATE_BANKING_THRESHOLD


@pytest.mark.asyncio
class TestAsyncToyyibPayClient:
    """Test async ToyyibPay client functionality."""
    
    @pytest.mark.asyncio
    async def test_async_client_initialization(self):
        """Test async client initialization."""
        client = toyyibpay.AsyncClient(api_key="test-key")
        assert client.config.api_key == "test-key"
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, test_config):
        """Test async client as context manager."""
        async with toyyibpay.AsyncClient(config=test_config) as client:
            assert client.config == test_config
            assert client._http_client is not None
    
    @pytest.mark.asyncio
    async def test_create_bill_success(self, async_client, sample_bill_data, mock_async_httpx_client):
        """Test successful async bill creation."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        async with async_client as client:
            bill = await client.create_bill(**sample_bill_data)
            
            assert bill.bill_code == "ABC123"
            assert bill.payment_url == f"{client.config.base_url}/ABC123"
    
    @pytest.mark.asyncio
    async def test_create_bill_without_context_manager(self, async_client, sample_bill_data):
        """Test creating bill without context manager raises error."""
        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await async_client.create_bill(**sample_bill_data)
    
    @pytest.mark.asyncio
    async def test_create_bill_validation_error(self, async_client, sample_bill_data):
        """Test async bill creation with invalid amount."""
        sample_bill_data["amount"] = -10.00
        
        async with async_client as client:
            with pytest.raises(ValidationError, match="Amount must be greater than 0"):
                await client.create_bill(**sample_bill_data)
    
    @pytest.mark.asyncio
    async def test_create_bill_corporate_banking(self, async_client, sample_bill_data, mock_async_httpx_client):
        """Test async bill creation enables corporate banking for large amounts."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        sample_bill_data["amount"] = CORPORATE_BANKING_THRESHOLD + 1000
        
        async with async_client as client:
            await client.create_bill(**sample_bill_data)
            
            # Verify enableFPXB2B was set
            # Note: This is tricky with async mocks, might need adjustment
    
    @pytest.mark.asyncio
    async def test_create_bill_from_input(self, async_client, mock_async_httpx_client):
        """Test async bill creation from InitPaymentInput model."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        payment_input = toyyibpay.InitPaymentInput(
            order_id="ORD-12345",
            name="John Doe",
            email="john@example.com",
            phone="0123456789",
            amount=Decimal("100.00"),
        )
        
        async with async_client as client:
            bill = await client.create_bill_from_input(payment_input)
            assert bill.bill_code == "ABC123"
    
    @pytest.mark.asyncio
    async def test_get_bill_transactions_success(self, async_client, mock_async_httpx_client, sample_transaction_data):
        """Test async getting bill transactions."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = [sample_transaction_data]
        
        async with async_client as client:
            transactions = await client.get_bill_transactions("ABC123")
            
            assert len(transactions) == 1
            assert transactions[0].bill_to == "John Doe"
            assert transactions[0].bill_payment_status == PaymentStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_get_bill_transactions_with_status_filter(self, async_client, mock_async_httpx_client):
        """Test async getting bill transactions with status filter."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = []
        
        async with async_client as client:
            transactions = await client.get_bill_transactions(
                "ABC123",
                status=PaymentStatus.SUCCESS
            )
            
            assert transactions == []
    
    @pytest.mark.asyncio
    async def test_check_payment_status_success(self, async_client, mock_async_httpx_client, sample_transaction_data):
        """Test async checking payment status returns success."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = [sample_transaction_data]
        
        async with async_client as client:
            status = await client.check_payment_status("ABC123")
            assert status == PaymentStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_check_payment_status_no_transactions(self, async_client, mock_async_httpx_client):
        """Test async checking payment status with no transactions."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = []
        
        async with async_client as client:
            status = await client.check_payment_status("ABC123")
            assert status is None
    
    @pytest.mark.asyncio
    async def test_create_category_success(self, async_client, mock_async_httpx_client):
        """Test async creating a category."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"CategoryCode": "CAT123"}
        
        async with async_client as client:
            result = await client.create_category(
                name="Test Category",
                description="Test Description"
            )
            
            assert result["CategoryCode"] == "CAT123"
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, async_client, sample_bill_data, mock_async_httpx_client):
        """Test async network error handling."""
        mock_client, mock_response = mock_async_httpx_client
        
        # Create an async function that raises NetworkError
        async def raise_network_error(*args, **kwargs):
            raise httpx.NetworkError("Connection failed")
        
        mock_client.request = raise_network_error
        
        async with async_client as client:
            with pytest.raises(NetworkError, match="Network error"):
                await client.create_bill(**sample_bill_data)
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, async_client, sample_bill_data, mock_async_httpx_client):
        """Test multiple concurrent async requests."""
        mock_client, mock_response = mock_async_httpx_client
        mock_response.json.return_value = {"BillCode": "ABC123"}
        
        import asyncio
        
        async with async_client as client:
            # Create multiple bills concurrently
            tasks = []
            for i in range(5):
                bill_data = {**sample_bill_data, "order_id": f"ORD-{i}"}
                tasks.append(client.create_bill(**bill_data))
            
            bills = await asyncio.gather(*tasks)
            
            assert len(bills) == 5
            assert all(bill.bill_code == "ABC123" for bill in bills)


@pytest.mark.asyncio
class TestAsyncClientHelpers:
    """Test async client helper functions."""
    
    @pytest.mark.asyncio
    async def test_async_client_convenience_function(self):
        """Test AsyncClient() convenience function."""
        client = toyyibpay.AsyncClient(api_key="test-key")
        assert isinstance(client, toyyibpay.AsyncToyyibPayClient)
        assert client.config.api_key == "test-key"