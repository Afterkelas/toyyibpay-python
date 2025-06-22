"""Tests for webhook handling."""

import json
from unittest.mock import Mock, patch

import pytest

from toyyibpay.webhooks.handler import WebhookHandler, create_webhook_response
from toyyibpay.models import CallbackData
from toyyibpay.enums import PaymentStatus
from toyyibpay.exceptions import WebhookError, SignatureVerificationError


class TestWebhookHandler:
    """Test webhook handler functionality."""
    
    @pytest.mark.unit
    def test_webhook_handler_initialization(self):
        """Test webhook handler initialization."""
        handler = WebhookHandler()
        assert handler.secret_key is None
        assert len(handler._handlers) == 4  # success, failed, pending, all
        
        handler_with_secret = WebhookHandler(secret_key="secret123")
        assert handler_with_secret.secret_key == "secret123"
    
    @pytest.mark.unit
    def test_register_payment_success_handler(self):
        """Test registering payment success handler."""
        handler = WebhookHandler()
        callback_called = False
        
        def on_success(data: CallbackData):
            nonlocal callback_called
            callback_called = True
        
        handler.on_payment_success(on_success)
        assert len(handler._handlers["payment.success"]) == 1
    
    @pytest.mark.unit
    def test_register_payment_failed_handler(self):
        """Test registering payment failed handler."""
        handler = WebhookHandler()
        
        def on_failed(data: CallbackData):
            pass
        
        handler.on_payment_failed(on_failed)
        assert len(handler._handlers["payment.failed"]) == 1
    
    @pytest.mark.unit
    def test_register_payment_pending_handler(self):
        """Test registering payment pending handler."""
        handler = WebhookHandler()
        
        def on_pending(data: CallbackData):
            pass
        
        handler.on_payment_pending(on_pending)
        assert len(handler._handlers["payment.pending"]) == 1
    
    @pytest.mark.unit
    def test_register_all_events_handler(self):
        """Test registering handler for all events."""
        handler = WebhookHandler()
        
        def on_all(data: CallbackData):
            pass
        
        handler.on_all_events(on_all)
        assert len(handler._handlers["all"]) == 1
    
    @pytest.mark.unit
    def test_process_webhook_success(self, sample_callback_data):
        """Test processing successful payment webhook."""
        handler = WebhookHandler()
        success_called = False
        all_called = False
        
        @handler.on_payment_success
        def on_success(data: CallbackData):
            nonlocal success_called
            success_called = True
            assert data.order_id == "ORD-12345"
            assert data.status == PaymentStatus.SUCCESS
        
        @handler.on_all_events
        def on_all(data: CallbackData):
            nonlocal all_called
            all_called = True
        
        result = handler.process(sample_callback_data)
        
        assert isinstance(result, CallbackData)
        assert result.order_id == "ORD-12345"
        assert success_called
        assert all_called
    
    @pytest.mark.unit
    def test_process_webhook_failed(self, sample_callback_data):
        """Test processing failed payment webhook."""
        handler = WebhookHandler()
        failed_called = False
        
        # Modify data for failed payment
        sample_callback_data["status"] = 3  # Failed
        sample_callback_data["reason"] = "Insufficient funds"
        
        @handler.on_payment_failed
        def on_failed(data: CallbackData):
            nonlocal failed_called
            failed_called = True
            assert data.status == PaymentStatus.FAILED
            assert data.reason == "Insufficient funds"
        
        result = handler.process(sample_callback_data)
        
        assert failed_called
        assert result.status == PaymentStatus.FAILED
    
    @pytest.mark.unit
    def test_process_webhook_pending(self, sample_callback_data):
        """Test processing pending payment webhook."""
        handler = WebhookHandler()
        pending_called = False
        
        sample_callback_data["status"] = 2  # Pending
        
        @handler.on_payment_pending
        def on_pending(data: CallbackData):
            nonlocal pending_called
            pending_called = True
            assert data.status == PaymentStatus.PENDING
        
        handler.process(sample_callback_data)
        assert pending_called
    
    @pytest.mark.unit
    def test_process_webhook_json_string(self, sample_callback_data):
        """Test processing webhook with JSON string payload."""
        handler = WebhookHandler()
        json_payload = json.dumps(sample_callback_data)
        
        result = handler.process(json_payload)
        assert result.order_id == "ORD-12345"
    
    @pytest.mark.unit
    def test_process_webhook_bytes(self, sample_callback_data):
        """Test processing webhook with bytes payload."""
        handler = WebhookHandler()
        bytes_payload = json.dumps(sample_callback_data).encode()
        
        result = handler.process(bytes_payload)
        assert result.order_id == "ORD-12345"
    
    @pytest.mark.unit
    def test_process_webhook_invalid_json(self):
        """Test processing webhook with invalid JSON."""
        handler = WebhookHandler()
        
        with pytest.raises(WebhookError, match="Invalid JSON payload"):
            handler.process("invalid json {")
    
    @pytest.mark.unit
    def test_process_webhook_invalid_data(self):
        """Test processing webhook with invalid data structure."""
        handler = WebhookHandler()
        invalid_data = {"invalid": "data"}
        
        with pytest.raises(WebhookError, match="Invalid callback data"):
            handler.process(invalid_data)
    
    @pytest.mark.unit
    def test_handler_exception_handling(self, sample_callback_data):
        """Test exception in handler doesn't stop processing."""
        handler = WebhookHandler()
        first_called = False
        second_called = False
        
        @handler.on_payment_success
        def failing_handler(data: CallbackData):
            nonlocal first_called
            first_called = True
            raise Exception("Handler error")
        
        @handler.on_payment_success
        def working_handler(data: CallbackData):
            nonlocal second_called
            second_called = True
        
        # Should not raise exception
        handler.process(sample_callback_data)
        
        assert first_called
        assert second_called
    
    @pytest.mark.unit
    def test_verify_signature_no_headers(self):
        """Test signature verification with no headers."""
        handler = WebhookHandler(secret_key="secret123")
        
        with pytest.raises(SignatureVerificationError, match="No headers provided"):
            handler._verify_signature("{}", None)
    
    @pytest.mark.unit
    def test_verify_signature_no_signature_header(self):
        """Test signature verification with missing signature header."""
        handler = WebhookHandler(secret_key="secret123")
        headers = {"Content-Type": "application/json"}
        
        with pytest.raises(SignatureVerificationError, match="No signature header found"):
            handler._verify_signature("{}", headers)
    
    @pytest.mark.unit
    def test_verify_signature_invalid_signature(self):
        """Test signature verification with invalid signature."""
        handler = WebhookHandler(secret_key="secret123")
        headers = {"X-ToyyibPay-Signature": "invalid_signature"}
        
        with pytest.raises(SignatureVerificationError, match="Invalid signature"):
            handler._verify_signature("{}", headers)
    
    @pytest.mark.unit
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        import hmac
        import hashlib
        
        handler = WebhookHandler(secret_key="secret123")
        payload = '{"test": "data"}'
        
        # Calculate correct signature
        expected_signature = hmac.new(
            b"secret123",
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        headers = {"X-ToyyibPay-Signature": expected_signature}
        
        # Should not raise exception
        handler._verify_signature(payload, headers)
    
    @pytest.mark.unit
    def test_process_with_signature_verification(self, sample_callback_data):
        """Test processing webhook with signature verification enabled."""
        handler = WebhookHandler(secret_key="secret123")
        
        # Without proper signature, should fail
        with pytest.raises(SignatureVerificationError):
            handler.process(sample_callback_data, headers={}, verify_signature=True)
    
    @pytest.mark.unit
    def test_get_event_type(self):
        """Test event type determination from status."""
        handler = WebhookHandler()
        
        assert handler._get_event_type(PaymentStatus.SUCCESS) == "payment.success"
        assert handler._get_event_type(PaymentStatus.FAILED) == "payment.failed"
        assert handler._get_event_type(PaymentStatus.PENDING) == "payment.pending"
        assert handler._get_event_type(PaymentStatus.PENDING_TRANSACTION) == "payment.pending"


class TestWebhookHelpers:
    """Test webhook helper functions."""
    
    @pytest.mark.unit
    def test_create_webhook_response_success(self):
        """Test creating successful webhook response."""
        response = create_webhook_response()
        
        assert response["success"] is True
        assert response["message"] == "OK"
        assert "timestamp" in response
    
    @pytest.mark.unit
    def test_create_webhook_response_failure(self):
        """Test creating failed webhook response."""
        response = create_webhook_response(success=False, message="Processing failed")
        
        assert response["success"] is False
        assert response["message"] == "Processing failed"
        assert "timestamp" in response
    
    @pytest.mark.unit
    def test_create_webhook_response_timestamp_format(self):
        """Test webhook response timestamp format."""
        response = create_webhook_response()
        
        # Should be ISO format
        timestamp = response["timestamp"]
        assert "T" in timestamp  # ISO format includes T separator
        
        # Should be parseable
        from datetime import datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))