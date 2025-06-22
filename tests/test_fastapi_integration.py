"""Integration tests for FastAPI application."""

from decimal import Decimal
from unittest.mock import patch, Mock, AsyncMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, EmailStr

import toyyibpay
from toyyibpay.models import CallbackData
from toyyibpay.webhooks import WebhookHandler
from tests.factories import (
    create_test_bill,
    CallbackDataFactory,
    InitPaymentInputFactory,
)


# Request/Response models
class CreatePaymentRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    amount: Decimal
    order_id: str = ""
    description: str = "Payment"


class PaymentStatusResponse(BaseModel):
    success: bool = True
    order_id: str
    status: str
    amount: Decimal
    payment_url: str = None


@pytest.fixture
def fastapi_app():
    """Create FastAPI application for testing."""
    app = FastAPI(title="ToyyibPay Test App")
    
    # Initialize clients
    toyyibpay_client = toyyibpay.Client(api_key="test-api-key")
    async_client = toyyibpay.AsyncClient(api_key="test-api-key")
    webhook_handler = WebhookHandler()
    
    # Store in app state
    app.state.toyyibpay_client = toyyibpay_client
    app.state.async_client = async_client
    app.state.webhook_handler = webhook_handler
    
    # Define routes
    @app.post("/api/payments/create", response_model=PaymentStatusResponse)
    async def create_payment(request: CreatePaymentRequest):
        try:
            bill = app.state.toyyibpay_client.create_bill(
                name=request.name,
                email=request.email,
                phone=request.phone,
                amount=request.amount,
                order_id=request.order_id or toyyibpay.utils.generate_order_id(),
                description=request.description,
            )
            
            return PaymentStatusResponse(
                order_id=request.order_id,
                status="pending",
                amount=request.amount,
                payment_url=bill.payment_url,
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/api/payments/create-async")
    async def create_payment_async(request: CreatePaymentRequest):
        try:
            async with app.state.async_client as client:
                bill = await client.create_bill(
                    name=request.name,
                    email=request.email,
                    phone=request.phone,
                    amount=request.amount,
                    order_id=request.order_id or toyyibpay.utils.generate_order_id(),
                )
                
                return {
                    "success": True,
                    "bill_code": bill.bill_code,
                    "payment_url": bill.payment_url,
                }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/payments/{order_id}/status")
    async def get_payment_status(order_id: str):
        # Mock implementation
        return PaymentStatusResponse(
            order_id=order_id,
            status="pending",
            amount=Decimal("100.00"),
        )
    
    @app.post("/webhooks/toyyibpay")
    async def webhook_callback(request: dict):
        try:
            callback_data = app.state.webhook_handler.process(request)
            return {"success": True, "message": "Webhook processed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "toyyibpay-fastapi"}
    
    return app


@pytest.fixture
def fastapi_client(fastapi_app) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(fastapi_app)


@pytest.mark.integration
class TestFastAPIIntegration:
    """Test FastAPI integration."""
    
    def test_health_check(self, fastapi_client):
        """Test health check endpoint."""
        response = fastapi_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch("toyyibpay.client.ToyyibPayClient.create_bill")
    def test_create_payment_success(self, mock_create_bill, fastapi_client):
        """Test successful payment creation."""
        # Mock response
        mock_bill = Mock()
        mock_bill.payment_url = "https://toyyibpay.com/ABC123"
        mock_bill.bill_code = "ABC123"
        mock_create_bill.return_value = mock_bill
        
        # Make request
        payment_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "0123456789",
            "amount": "100.00",
            "order_id": "ORD-12345",
        }
        
        response = fastapi_client.post("/api/payments/create", json=payment_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["order_id"] == "ORD-12345"
        assert data["status"] == "pending"
        assert data["payment_url"] == "https://toyyibpay.com/ABC123"
    
    @patch("toyyibpay.client.ToyyibPayClient.create_bill")
    def test_create_payment_validation_error(self, mock_create_bill, fastapi_client):
        """Test payment creation with validation error."""
        mock_create_bill.side_effect = ValueError("Invalid amount")
        
        payment_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "0123456789",
            "amount": "-10.00",
        }
        
        response = fastapi_client.post("/api/payments/create", json=payment_data)
        
        assert response.status_code == 400
        assert "Invalid amount" in response.json()["detail"]
    
    def test_create_payment_invalid_email(self, fastapi_client):
        """Test payment creation with invalid email."""
        payment_data = {
            "name": "Test User",
            "email": "invalid-email",
            "phone": "0123456789",
            "amount": "100.00",
        }
        
        response = fastapi_client.post("/api/payments/create", json=payment_data)
        
        assert response.status_code == 422  # Validation error
        errors = response.json()["detail"]
        assert any("email" in str(error).lower() for error in errors)
    
    @patch("toyyibpay.async_client.AsyncToyyibPayClient.create_bill")
    @pytest.mark.asyncio
    async def test_create_payment_async(self, mock_create_bill, fastapi_client):
        """Test async payment creation."""
        # Mock async response
        mock_bill = Mock()
        mock_bill.payment_url = "https://toyyibpay.com/ABC123"
        mock_bill.bill_code = "ABC123"
        mock_create_bill.return_value = mock_bill
        
        payment_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "0123456789",
            "amount": "100.00",
        }
        
        response = fastapi_client.post("/api/payments/create-async", json=payment_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["bill_code"] == "ABC123"
    
    def test_get_payment_status(self, fastapi_client):
        """Test getting payment status."""
        response = fastapi_client.get("/api/payments/ORD-12345/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "ORD-12345"
        assert data["status"] == "pending"
    
    def test_webhook_callback(self, fastapi_client, fastapi_app):
        """Test webhook callback."""
        handler_called = False
        
        @fastapi_app.state.webhook_handler.on_payment_success
        def on_success(data: CallbackData):
            nonlocal handler_called
            handler_called = True
        
        webhook_data = CallbackDataFactory.create(status=1)
        response = fastapi_client.post("/webhooks/toyyibpay", json=webhook_data)
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert handler_called
    
    def test_webhook_callback_error(self, fastapi_client):
        """Test webhook callback with invalid data."""
        response = fastapi_client.post(
            "/webhooks/toyyibpay",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data


@pytest.mark.integration
class TestFastAPIMiddleware:
    """Test FastAPI middleware and features."""
    
    def test_request_validation(self, fastapi_client):
        """Test request validation."""
        # Missing required fields
        response = fastapi_client.post(
            "/api/payments/create",
            json={"name": "Test"}
        )
        
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert len(errors) > 0
    
    def test_response_model_validation(self, fastapi_client):
        """Test response model validation."""
        response = fastapi_client.get("/api/payments/ORD-12345/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        assert "success" in data
        assert "order_id" in data
        assert "status" in data
        assert "amount" in data
    
    def test_cors_middleware(self, fastapi_app):
        """Test CORS middleware if configured."""
        from fastapi.middleware.cors import CORSMiddleware
        
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        client = TestClient(fastapi_app)
        response = client.options("/health")
        
        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
    
    def test_exception_handling(self, fastapi_app):
        """Test exception handling."""
        @fastapi_app.get("/test-error")
        async def test_error():
            raise Exception("Test error")
        
        @fastapi_app.exception_handler(Exception)
        async def exception_handler(request, exc):
            return {"error": str(exc)}, 500
        
        client = TestClient(fastapi_app)
        response = client.get("/test-error")
        
        # FastAPI returns 500 by default for unhandled exceptions
        assert response.status_code == 500


@pytest.mark.integration
class TestFastAPIBackground:
    """Test FastAPI background tasks."""
    
    def test_background_task(self, fastapi_app):
        """Test background task execution."""
        from fastapi import BackgroundTasks
        
        task_executed = False
        
        @fastapi_app.post("/test-background")
        async def test_background(background_tasks: BackgroundTasks):
            def run_task():
                nonlocal task_executed
                task_executed = True
            
            background_tasks.add_task(run_task)
            return {"message": "Task scheduled"}
        
        client = TestClient(fastapi_app)
        response = client.post("/test-background")
        
        assert response.status_code == 200
        # Background tasks run after response in test client
        assert task_executed


@pytest.mark.integration
@pytest.mark.asyncio
class TestFastAPIAsync:
    """Test async features."""
    
    async def test_concurrent_requests(self, fastapi_client):
        """Test handling concurrent requests."""
        import asyncio
        
        async def make_request():
            return fastapi_client.get("/health")
        
        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(5)]
        responses = await asyncio.gather(*[asyncio.create_task(task) for task in tasks])
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
    
    async def test_async_context_manager(self, fastapi_app):
        """Test async context manager usage."""
        
        @fastapi_app.get("/test-async-client")
        async def test_async_client():
            async with fastapi_app.state.async_client as client:
                # Mock the check_payment_status method
                client.check_payment_status = AsyncMock(
                    return_value=toyyibpay.PaymentStatus.SUCCESS
                )
                
                status = await client.check_payment_status("ABC123")
                return {"status": status.name}
        
        client = TestClient(fastapi_app)
        response = client.get("/test-async-client")
        
        assert response.status_code == 200
        assert response.json()["status"] == "SUCCESS"