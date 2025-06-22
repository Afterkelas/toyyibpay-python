"""Pytest configuration and shared fixtures."""

import os
import json
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import toyyibpay
from toyyibpay.config import ToyyibPayConfig
from toyyibpay.enums import PaymentStatus, PaymentChannel
from toyyibpay.db.postgres import PostgresPaymentStore, Base


# Test configuration
TEST_API_KEY = "test-api-key-12345"
TEST_CATEGORY_ID = "test-cat-123"
TEST_BASE_URL = "https://dev.toyyibpay.com"


@pytest.fixture
def test_config() -> ToyyibPayConfig:
    """Create test configuration."""
    return ToyyibPayConfig(
        api_key=TEST_API_KEY,
        category_id=TEST_CATEGORY_ID,
        environment="dev",
        dev_base_url=TEST_BASE_URL,
        return_url="https://test.com/return",
        callback_url="https://test.com/callback",
        timeout=5.0,
        verify_ssl=False,
    )


@pytest.fixture
def client(test_config: ToyyibPayConfig) -> toyyibpay.Client:
    """Create test client."""
    return toyyibpay.Client(config=test_config)


@pytest.fixture
async def async_client(test_config: ToyyibPayConfig) -> toyyibpay.AsyncClient:
    """Create async test client."""
    return toyyibpay.AsyncClient(config=test_config)


@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Mock httpx client for testing."""
    mock_client = Mock(spec=httpx.Client)
    mock_response = Mock(spec=httpx.Response)
    
    # Default successful response
    mock_response.status_code = 200
    mock_response.json.return_value = {"BillCode": "test123"}
    mock_response.raise_for_status.return_value = None
    
    mock_client.request.return_value = mock_response
    
    # Patch the client creation
    monkeypatch.setattr("httpx.Client", lambda **kwargs: mock_client)
    
    return mock_client, mock_response


@pytest.fixture
def mock_async_httpx_client(monkeypatch):
    """Mock async httpx client for testing."""
    mock_client = Mock(spec=httpx.AsyncClient)
    mock_response = Mock(spec=httpx.Response)
    
    # Default successful response
    mock_response.status_code = 200
    mock_response.json.return_value = {"BillCode": "test123"}
    mock_response.raise_for_status.return_value = None
    
    # Make request async
    async def mock_request(*args, **kwargs):
        return mock_response
    
    mock_client.request = mock_request
    mock_client.aclose = Mock(return_value=None)
    
    # Patch the client creation
    monkeypatch.setattr("httpx.AsyncClient", lambda **kwargs: mock_client)
    
    return mock_client, mock_response


@pytest.fixture
def sample_bill_data() -> Dict[str, Any]:
    """Sample bill creation data."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "0123456789",
        "amount": 100.00,
        "order_id": "ORD-12345",
        "description": "Test payment",
    }


@pytest.fixture
def sample_callback_data() -> Dict[str, Any]:
    """Sample webhook callback data."""
    return {
        "refno": "REF123456",
        "order_id": "ORD-12345",
        "billcode": "test123",
        "status": 1,  # Success
        "reason": "",
        "amount": 10000,  # In cents
        "transaction_time": "2024-01-15 10:30:00",
    }


@pytest.fixture
def sample_transaction_data() -> Dict[str, Any]:
    """Sample transaction data."""
    return {
        "billName": "BILL123",
        "billDescription": "Test payment",
        "billTo": "John Doe",
        "billEmail": "john@example.com",
        "billPhone": "0123456789",
        "billStatus": "1",
        "billpaymentStatus": "1",
        "billpaymentAmount": "100.00",
        "billPaymentDate": "15-01-2024 10:30:00",
        "billpaymentChannel": "FPX",
        "billpaymentInvoiceNo": "INV123",
        "billExternalReferenceNo": "ORD-12345",
        "billSplitPayment": "0",
    }


@pytest.fixture
def db_engine():
    """Create test database engine."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create database session for tests."""
    from sqlalchemy.orm import sessionmaker
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def payment_store(db_engine) -> PostgresPaymentStore:
    """Create payment store for tests."""
    return PostgresPaymentStore(db_engine)


@pytest.fixture
def mock_ulid(monkeypatch) -> str:
    """Mock ULID generation."""
    test_ulid = "01HK3J4K5L6M7N8P9QRSTUVWXY"
    monkeypatch.setattr("toyyibpay.utils.generate_ulid", lambda: test_ulid)
    return test_ulid


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""
    test_datetime = datetime(2024, 1, 15, 10, 30, 0)
    
    class MockDatetime:
        @classmethod
        def now(cls):
            return test_datetime
        
        @classmethod
        def utcnow(cls):
            return test_datetime
    
    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return test_datetime


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global configuration after each test."""
    yield
    # Reset global config
    if hasattr(toyyibpay.config, "_global_config"):
        toyyibpay.config._global_config = None


@pytest.fixture
def env_vars(monkeypatch):
    """Set environment variables for testing."""
    env_vars = {
        "TOYYIBPAY_API_KEY": TEST_API_KEY,
        "TOYYIBPAY_CATEGORY_ID": TEST_CATEGORY_ID,
        "TOYYIBPAY_ENVIRONMENT": "dev",
        "TOYYIBPAY_RETURN_URL": "https://test.com/return",
        "TOYYIBPAY_CALLBACK_URL": "https://test.com/callback",
        "DATABASE_URL": "postgresql://test:test@localhost/test",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


# Markers for test organization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "async: Async tests")
    config.addinivalue_line("markers", "db: Database tests")
    config.addinivalue_line("markers", "slow: Slow tests")