"""Tests for exception handling in ToyyibPay SDK."""

import json
from unittest.mock import patch, Mock

import pytest
import httpx

import toyyibpay
from toyyibpay.exceptions import (
    ToyyibPayError,
    ConfigurationError,
    AuthenticationError,
    APIError,
    ValidationError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    InvalidRequestError,
    PaymentError,
    WebhookError,
    SignatureVerificationError,
    DatabaseError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy."""
    
    def test_base_exception(self):
        """Test base ToyyibPayError."""
        error = ToyyibPayError(
            message="Test error",
            code="TEST001",
            status_code=400,
            response={"detail": "Test"}
        )
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.code == "TEST001"
        assert error.status_code == 400
        assert error.response == {"detail": "Test"}
    
    def test_exception_inheritance(self):
        """Test all exceptions inherit from ToyyibPayError."""
        exceptions = [
            ConfigurationError("Config error"),
            AuthenticationError("Auth error"),
            APIError("API error"),
            ValidationError("Validation error"),
            NetworkError("Network error"),
            TimeoutError("Timeout error"),
            RateLimitError("Rate limit error"),
            InvalidRequestError("Invalid request"),
            PaymentError("Payment error"),
            WebhookError("Webhook error"),
            SignatureVerificationError("Signature error"),
            DatabaseError("Database error"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, ToyyibPayError)
            assert isinstance(exc, Exception)


class TestConfigurationErrors:
    """Test configuration-related errors."""
    
    def test_missing_api_key(self):
        """Test error when API key is missing."""
        with pytest.raises(ValueError, match="API key is required"):
            toyyibpay.ToyyibPayConfig(api_key="")
    
    def test_invalid_environment(self):
        """Test handling invalid environment."""
        # Environment is a string, so any value is accepted
        # But base URL selection should handle unknown environments
        config = toyyibpay.ToyyibPayConfig(
            api_key="test-key",
            environment="unknown"
        )
        # Should default to dev URL for non-production
        assert config.base_url == config.dev_base_url
    
    def test_missing_global_config(self):
        """Test error when global config not set."""
        # Ensure global config is not set
        toyyibpay.config._global_config = None
        
        with pytest.raises(RuntimeError, match="configuration not set"):
            toyyibpay.Client()


class TestValidationErrors:
    """Test validation errors."""
    
    def test_invalid_amount(self, test_config):
        """Test validation error for invalid amount."""
        client = toyyibpay.Client(config=test_config)
        
        with pytest.raises(ValidationError, match="Amount must be greater than 0"):
            client.create_bill(
                name="Test",
                email="test@example.com",
                phone="0123456789",
                amount=-10.00,
                order_id="TEST-001"
            )
    
    def test_invalid_email_format(self):
        """Test validation error for invalid email."""
        with pytest.raises(Exception) as exc_info:  # Pydantic raises its own error
            toyyibpay.InitPaymentInput(
                order_id="TEST-001",
                name="Test User",
                email="invalid-email",
                phone="0123456789",
                amount=100.00
            )
        
        assert "email" in str(exc_info.value).lower()
    
    def test_invalid_bill_name(self):
        """Test validation error for invalid bill name."""
        with pytest.raises(Exception) as exc_info:
            toyyibpay.CreateBillInput(
                category_code="CAT123",
                bill_name="Invalid@Name!",  # Contains invalid characters
                bill_description="Test",
                bill_amount=100.00,
                bill_return_url="https://example.com",
                bill_callback_url="https://example.com",
                bill_external_reference_no="TEST-001",
                bill_to="Test User",
                bill_email="test@example.com",
                bill_phone="0123456789"
            )
        
        assert "alphanumeric" in str(exc_info.value)


class TestHTTPErrors:
    """Test HTTP-related errors."""
    
    @patch("httpx.Client.request")
    def test_authentication_error(self, mock_request, test_config):
        """Test authentication error (401)."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=Mock(),
            response=mock_response
        )
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationError) as exc_info:
            client.create_bill(
                name="Test",
                email="test@example.com",
                phone="0123456789",
                amount=100.00,
                order_id="TEST-001"
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)
    
    @patch("httpx.Client.request")
    def test_rate_limit_error(self, mock_request, test_config):
        """Test rate limit error (429)."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=Mock(),
            response=mock_response
        )
        mock_request.return_value = mock_response
        
        with pytest.raises(RateLimitError) as exc_info:
            client.get_bill_transactions("ABC123")
        
        assert exc_info.value.status_code == 429
    
    @patch("httpx.Client.request")
    def test_server_error(self, mock_request, test_config):
        """Test server error (500)."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Internal server error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=Mock(),
            response=mock_response
        )
        mock_request.return_value = mock_response
        
        with pytest.raises(APIError) as exc_info:
            client.create_category("Test", "Description")
        
        assert exc_info.value.status_code == 500
        assert "Server error" in str(exc_info.value)
    
    @patch("httpx.Client.request")
    def test_network_error(self, mock_request, test_config):
        """Test network connection error."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock network error
        mock_request.side_effect = httpx.NetworkError("Connection refused")
        
        with pytest.raises(NetworkError) as exc_info:
            client.create_bill(
                name="Test",
                email="test@example.com",
                phone="0123456789",
                amount=100.00,
                order_id="TEST-001"
            )
        
        assert "Network error" in str(exc_info.value)
    
    @patch("httpx.Client.request")
    def test_timeout_error(self, mock_request, test_config):
        """Test request timeout error."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock timeout
        mock_request.side_effect = httpx.TimeoutException("Request timed out")
        
        with pytest.raises(TimeoutError) as exc_info:
            client.check_payment_status("ABC123")
        
        assert "Request timed out" in str(exc_info.value)


class TestWebhookErrors:
    """Test webhook-related errors."""
    
    def test_invalid_webhook_json(self):
        """Test webhook error with invalid JSON."""
        handler = toyyibpay.WebhookHandler()
        
        with pytest.raises(WebhookError, match="Invalid JSON payload"):
            handler.process("invalid{json")
    
    def test_invalid_webhook_data(self):
        """Test webhook error with invalid data structure."""
        handler = toyyibpay.WebhookHandler()
        
        with pytest.raises(WebhookError, match="Invalid callback data"):
            handler.process({"invalid": "structure"})
    
    def test_signature_verification_no_headers(self):
        """Test signature verification error with no headers."""
        handler = toyyibpay.WebhookHandler(secret_key="secret123")
        
        with pytest.raises(SignatureVerificationError, match="No headers provided"):
            handler.process("{}", headers=None, verify_signature=True)
    
    def test_signature_verification_invalid(self):
        """Test signature verification error with invalid signature."""
        handler = toyyibpay.WebhookHandler(secret_key="secret123")
        
        with pytest.raises(SignatureVerificationError, match="Invalid signature"):
            handler.process(
                "{}",
                headers={"X-ToyyibPay-Signature": "invalid"},
                verify_signature=True
            )
    
    def test_webhook_handler_exception(self):
        """Test exception in webhook handler doesn't propagate."""
        handler = toyyibpay.WebhookHandler()
        
        @handler.on_payment_success
        def failing_handler(data):
            raise Exception("Handler error")
        
        # Should not raise exception
        from tests.factories import CallbackDataFactory
        webhook_data = CallbackDataFactory.create(status=1)
        
        # Process should succeed despite handler error
        result = handler.process(webhook_data)
        assert result is not None


class TestDatabaseErrors:
    """Test database-related errors."""
    
    def test_database_connection_error(self):
        """Test database connection error."""
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        
        # Invalid database URL
        try:
            engine = create_engine("postgresql://invalid:invalid@nonexistent:5432/db")
            from toyyibpay.db.postgres import PostgresPaymentStore
            
            store = PostgresPaymentStore(engine)
            with store.session() as session:
                # This should fail
                store.create_payment(
                    session,
                    order_id="TEST-001",
                    amount=100.00,
                    bill_code="ABC123"
                )
        except OperationalError:
            # Expected error
            pass
    
    def test_database_integrity_error(self, db_engine):
        """Test database integrity constraint violation."""
        from sqlalchemy.exc import IntegrityError
        from toyyibpay.db.postgres import PostgresPaymentStore
        
        store = PostgresPaymentStore(db_engine)
        store.create_tables()
        
        # Create first payment
        with store.session() as session:
            store.create_payment(
                session,
                order_id="DUP-001",
                amount=100.00,
                bill_code="ABC123"
            )
        
        # Try to create duplicate
        with pytest.raises(IntegrityError):
            with store.session() as session:
                store.create_payment(
                    session,
                    order_id="DUP-001",  # Duplicate order ID
                    amount=200.00,
                    bill_code="DEF456"
                )
    
    def test_database_rollback(self, db_engine):
        """Test database transaction rollback on error."""
        from toyyibpay.db.postgres import PostgresPaymentStore
        
        store = PostgresPaymentStore(db_engine)
        store.create_tables()
        
        try:
            with store.session() as session:
                # Create payment
                payment = store.create_payment(
                    session,
                    order_id="ROLLBACK-001",
                    amount=100.00,
                    bill_code="RB123"
                )
                
                # Force error before commit
                raise Exception("Forced error")
        except Exception:
            pass
        
        # Verify payment was rolled back
        with store.session() as session:
            payment = store.get_payment_by_order_id(session, "ROLLBACK-001")
            assert payment is None


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    @patch("httpx.Client.request")
    def test_retry_after_network_error(self, mock_request, test_config):
        """Test manual retry after network error."""
        client = toyyibpay.Client(config=test_config)
        
        # First call fails, second succeeds
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise httpx.NetworkError("Connection failed")
            
            # Second call succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"BillCode": "RETRY123"}
            mock_response.raise_for_status.return_value = None
            return mock_response
        
        mock_request.side_effect = side_effect
        
        # First attempt
        with pytest.raises(NetworkError):
            client.create_bill(
                name="Test",
                email="test@example.com",
                phone="0123456789",
                amount=100.00,
                order_id="RETRY-001"
            )
        
        # Retry
        bill = client.create_bill(
            name="Test",
            email="test@example.com",
            phone="0123456789",
            amount=100.00,
            order_id="RETRY-001"
        )
        
        assert bill.bill_code == "RETRY123"
        assert call_count == 2
    
    def test_graceful_degradation(self, test_config):
        """Test graceful degradation when optional features fail."""
        client = toyyibpay.Client(config=test_config)
        
        # Even if optional features fail, core should work
        with patch.object(client._http_client, "post") as mock_post:
            mock_post.return_value = {"BillCode": "GRACEFUL123"}
            
            # Create bill with minimal required fields
            bill = client.create_bill(
                name="Test",
                email="test@example.com",
                phone="0123456789",
                amount=100.00,
                order_id="GRACEFUL-001"
            )
            
            assert bill.bill_code == "GRACEFUL123"