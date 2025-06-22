# ToyyibPay Python SDK - Architecture & Design Guide

This document describes the architecture, design patterns, and development practices of the ToyyibPay Python SDK. It's intended for contributors who want to understand how the SDK is built and how to extend it.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Design Principles](#design-principles)
- [Architecture Patterns](#architecture-patterns)
- [Core Components](#core-components)
- [Testing Architecture](#testing-architecture)
- [Development Environment](#development-environment)
- [Code Quality Standards](#code-quality-standards)
- [Extension Points](#extension-points)

## Overview

The ToyyibPay Python SDK is designed as a modern, type-safe, and extensible payment gateway integration library. It provides both synchronous and asynchronous interfaces, supports multiple web frameworks, and includes optional database integration.

### Key Features

- **Dual Interface**: Both sync (`Client`) and async (`AsyncClient`) implementations
- **Type Safety**: Full type hints with Pydantic models
- **Framework Agnostic**: Core SDK with framework-specific adapters
- **Extensible**: Plugin architecture for resources and storage backends
- **Test-Driven**: Comprehensive test suite with 95%+ coverage

## Directory Structure

```
toyyibpay/
├── __init__.py          # Public API exports
├── client.py            # Synchronous client implementation
├── async_client.py      # Asynchronous client implementation
├── config.py            # Configuration management
├── models.py            # Pydantic data models
├── enums.py             # Enumeration constants
├── exceptions.py        # Custom exception hierarchy
├── http_client.py       # HTTP transport layer
├── utils.py             # Utility functions
│
├── resources/           # Resource-based API organization
│   ├── base.py         # Base resource class
│   ├── bills.py        # Bill management resources
│   ├── categories.py   # Category resources
│   └── transactions.py # Transaction resources
│
├── webhooks/            # Webhook handling
│   ├── handler.py      # Core webhook processor
│   ├── flask.py        # Flask integration
│   └── fastapi.py      # FastAPI integration
│
└── db/                  # Database layer (optional)
    ├── base.py         # Abstract base store
    ├── postgres.py     # PostgreSQL implementation
    └── models.py       # SQLAlchemy models
```

## Design Principles

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:

```python
# HTTP transport is separate from business logic
http_client.py  # Handles HTTP communication
client.py       # Implements business logic
models.py       # Defines data structures
```

### 2. DRY (Don't Repeat Yourself)

Shared functionality is abstracted into reusable components:

```python
# Base HTTP client used by both sync and async clients
class BaseHTTPClient:
    def _prepare_data(self, data: Optional[Dict] = None) -> Dict:
        """Shared data preparation logic."""
        request_data = {"userSecretKey": self.config.api_key}
        if data:
            request_data.update(data)
        return request_data

# Sync and async clients share the same business logic
class ClientMixin:
    def _prepare_bill_data(self, amount: Decimal) -> Dict:
        """Shared bill preparation logic."""
        # Used by both ToyyibPayClient and AsyncToyyibPayClient
```

### 3. Extensibility

The SDK is designed to be extended without modifying core code:

```python
# New payment channels can be added via enums
class PaymentChannel(IntEnum):
    FPX = 0
    CREDIT_CARD = 1
    # Easy to add: EWALLET = 3

# New storage backends via abstract base
class PaymentStore(ABC):
    @abstractmethod
    def create_payment(self, ...): pass
    
# Implement for any database
class MongoPaymentStore(PaymentStore):
    def create_payment(self, ...): 
        # MongoDB implementation
```

### 4. Explicit Over Implicit

Configuration and behavior are explicit:

```python
# Explicit configuration
client = Client(
    api_key="...",
    environment="production",
    timeout=30.0
)

# Not implicit global state
# ❌ toyyibpay.api_key = "..."
# ✅ client = Client(api_key="...")
```

## Architecture Patterns

### 1. Client Factory Pattern

The SDK provides factory functions for easy client creation:

```python
# Factory functions in __init__.py
def Client(api_key: Optional[str] = None, **kwargs) -> ToyyibPayClient:
    """Factory for creating sync client."""
    return ToyyibPayClient(api_key=api_key, **kwargs)

def AsyncClient(api_key: Optional[str] = None, **kwargs) -> AsyncToyyibPayClient:
    """Factory for creating async client."""
    return AsyncToyyibPayClient(api_key=api_key, **kwargs)
```

### 2. Strategy Pattern for HTTP Transport

Different HTTP strategies for sync vs async:

```python
# Abstract interface
class BaseHTTPTransport:
    def request(self, method: str, url: str, **kwargs) -> Response:
        raise NotImplementedError

# Concrete implementations
class SyncHTTPTransport(BaseHTTPTransport):
    def request(self, method: str, url: str, **kwargs) -> Response:
        return httpx.request(method, url, **kwargs)

class AsyncHTTPTransport(BaseHTTPTransport):
    async def request(self, method: str, url: str, **kwargs) -> Response:
        async with httpx.AsyncClient() as client:
            return await client.request(method, url, **kwargs)
```

### 3. Resource-Based Architecture

APIs are organized as resources (similar to Stripe SDK):

```python
# Base resource pattern
class BaseResource:
    def __init__(self, client: BaseClient):
        self.client = client
    
    def _request(self, method: str, path: str, **kwargs):
        return self.client.request(method, path, **kwargs)

# Specific resources
class Bills(BaseResource):
    def create(self, **data) -> BillResponse:
        return self._request("POST", "/createBill", data=data)
    
    def get(self, bill_code: str) -> Bill:
        return self._request("GET", f"/getBill/{bill_code}")
```

### 4. Adapter Pattern for Webhooks

Framework-specific adapters for webhook handling:

```python
# Core webhook handler
class WebhookHandler:
    def process(self, payload: Union[str, bytes, Dict]) -> CallbackData:
        # Framework-agnostic processing
        
# Framework adapters
class FlaskWebhookAdapter:
    def __init__(self, handler: WebhookHandler):
        self.handler = handler
    
    def route(self):
        @app.route("/webhook", methods=["POST"])
        def webhook():
            return self.handler.process(request.data)

class FastAPIWebhookAdapter:
    def __init__(self, handler: WebhookHandler):
        self.handler = handler
    
    @app.post("/webhook")
    async def webhook(self, request: Request):
        body = await request.body()
        return self.handler.process(body)
```

## Core Components

### 1. Configuration Management

Centralized configuration with environment variable support:

```python
# config.py
@dataclass
class ToyyibPayConfig:
    api_key: str
    environment: Environment = Environment.PRODUCTION
    
    @classmethod
    def from_env(cls, **kwargs) -> "ToyyibPayConfig":
        """Load from environment variables."""
        return cls(
            api_key=os.getenv("TOYYIBPAY_API_KEY", kwargs.get("api_key", "")),
            environment=os.getenv("TOYYIBPAY_ENVIRONMENT", "production"),
            **kwargs
        )
```

### 2. Model Validation

Pydantic models with automatic validation:

```python
# models.py
class CreateBillInput(BaseModel):
    bill_amount: float = Field(..., gt=0)
    bill_email: EmailStr
    
    @field_validator("bill_amount")
    @classmethod
    def convert_to_cents(cls, v: float) -> float:
        """Auto-convert to smallest currency unit."""
        return v * 100
```

### 3. Error Handling Hierarchy

Structured exception hierarchy:

```python
# exceptions.py
ToyyibPayError          # Base exception
├── ConfigurationError  # Config issues
├── ValidationError     # Data validation
├── APIError           # API responses
│   ├── AuthenticationError  # 401
│   ├── RateLimitError      # 429
│   └── ServerError         # 5xx
└── NetworkError       # Connection issues
```

## Testing Architecture

### 1. Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── factories.py             # Test data factories
├── mock_server.py           # Mock API server
│
├── test_*.py               # Unit tests
├── test_*_integration.py   # Integration tests
└── test_benchmarks.py      # Performance tests
```

### 2. Fixture Design

Layered fixtures for different test scenarios:

```python
# conftest.py
@pytest.fixture
def test_config():
    """Test configuration."""
    return ToyyibPayConfig(api_key="test-key")

@pytest.fixture
def client(test_config):
    """Configured test client."""
    return Client(config=test_config)

@pytest.fixture
def mock_http_response(monkeypatch):
    """Mock HTTP responses."""
    def _mock(status=200, json_data=None):
        mock_resp = Mock()
        mock_resp.status_code = status
        mock_resp.json.return_value = json_data
        return mock_resp
    return _mock
```

### 3. Test Categories

Tests are organized by markers:

```python
@pytest.mark.unit       # Fast, isolated tests
@pytest.mark.integration # External dependencies
@pytest.mark.async      # Async functionality
@pytest.mark.slow       # Long-running tests
@pytest.mark.benchmark  # Performance tests
```

### 4. Mock Server

Complete mock ToyyibPay server for integration testing:

```python
# mock_server.py
class MockToyyibPayServer:
    def __init__(self, port: int = 5555):
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route("/index.php/api/createBill", methods=["POST"])
        def create_bill():
            # Mock implementation
```

## Development Environment

### 1. Environment Configuration

`.env.example` provides template for local development:

```bash
# .env.example
TOYYIBPAY_API_KEY=your-secret-key-here
TOYYIBPAY_CATEGORY_ID=your-category-id
TOYYIBPAY_ENVIRONMENT=dev
DATABASE_URL=postgresql://user:pass@localhost/db
```

### 2. Development Installation

```bash
# Clone and install with all dev dependencies
git clone https://github.com/mwaizwafiq/toyyibpay-python.git
cd toyyibpay-python
pip install -e ".[dev,postgres,flask,fastapi]"

# Install pre-commit hooks
pre-commit install
```

### 3. Multi-Environment Testing (tox)

`tox.ini` configures testing across Python versions:

```ini
[tox]
envlist = py{38,39,310,311,312}

[testenv]
deps = pytest>=7.0.0
commands = pytest {posargs:tests}

[testenv:py{38,39,310,311,312}-postgres]
extras = postgres
commands = pytest {posargs:tests} -m "db"
```

## Code Quality Standards

### 1. Formatting (Black)

Consistent code formatting with Black:

```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
```

### 2. Import Sorting (isort)

Organized imports:

```python
# pyproject.toml
[tool.isort]
profile = "black"
multi_line_output = 3
```

### 3. Linting (Flake8)

Code quality checks:

```ini
# setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503  # Black compatibility
exclude = .git,__pycache__,build,dist
```

### 4. Type Checking (MyPy)

Static type checking:

```python
# pyproject.toml
[tool.mypy]
python_version = "3.8"
disallow_untyped_defs = true
warn_return_any = true
```

### 5. Pre-commit Hooks

Automated checks before commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    hooks:
      - id: flake8
```

## Extension Points

### 1. Adding New Resources

Create new resource modules:

```python
# resources/refunds.py
from .base import BaseResource

class Refunds(BaseResource):
    def create(self, bill_code: str, amount: float) -> RefundResponse:
        return self._request("POST", "/createRefund", {
            "billCode": bill_code,
            "amount": amount
        })
```

### 2. Adding Storage Backends

Implement the abstract store:

```python
# db/redis.py
from .base import PaymentStore

class RedisPaymentStore(PaymentStore):
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)
    
    def create_payment(self, payment_data: Dict) -> str:
        payment_id = generate_ulid()
        self.redis.hset(f"payment:{payment_id}", payment_data)
        return payment_id
```

### 3. Adding Framework Support

Create framework-specific integrations:

```python
# webhooks/django.py
from django.http import JsonResponse
from django.views import View

class ToyyibPayWebhookView(View):
    def __init__(self, handler: WebhookHandler):
        self.handler = handler
    
    def post(self, request):
        result = self.handler.process(request.body)
        return JsonResponse({"success": True})
```

## Contributing Guidelines

### 1. Code Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Write tests first (TDD)
4. Implement your feature
5. Ensure all tests pass: `pytest`
6. Run code quality checks: `make lint`
7. Commit with clear messages
8. Push and create a PR

### 2. Testing Requirements

- All new features must have tests
- Maintain >95% code coverage
- Add integration tests for external interactions
- Include docstring examples

### 3. Documentation

- Update docstrings with Google style
- Add usage examples in docstrings
- Update README for user-facing changes
- Update ARCHITECTURE.md for design changes

### 4. Review Process

1. Automated CI must pass
2. Code review by maintainer
3. Address feedback
4. Squash commits if requested
5. Merge via "Squash and merge"

