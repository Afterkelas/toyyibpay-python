"""
ToyyibPay Python SDK

A modern, easy-to-use Python SDK for integrating with ToyyibPay payment gateway.

Basic Usage:
    >>> import toyyibpay
    >>> client = toyyibpay.Client(api_key="your-api-key")
    >>> bill = client.create_bill(
    ...     name="John Doe",
    ...     email="john@example.com",
    ...     phone="0123456789",
    ...     amount=100.00,
    ...     order_id="ORD-12345"
    ... )
    >>> print(bill.payment_url)

For more examples, see the documentation at https://github.com/waizwafiq/toyyibpay-python
"""

from . import utils
from .client import ToyyibPayClient, Client
from .async_client import AsyncToyyibPayClient, AsyncClient
from .config import ToyyibPayConfig, set_config, get_config
from .enums import (
    PaymentStatus,
    PaymentChannel,
    ChargeParty,
    PriceVariable,
    PayerInfo,
    Environment,
)
from .exceptions import (
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
from .models import (
    CreateBillInput,
    BillResponse,
    CallbackData,
    TransactionData,
    PaymentRecord,
    APIResponse,
    InitPaymentInput,
    CategoryInput,
)
from .webhooks.handler import WebhookHandler, create_webhook_response

# Version
__version__ = "0.1.0"

# Public API
__all__ = [
    # Main client
    "Client",
    "ToyyibPayClient",
    "AsyncClient",
    "AsyncToyyibPayClient",
    
    # Configuration
    "ToyyibPayConfig",
    "set_config",
    "get_config",
    
    # Enums
    "PaymentStatus",
    "PaymentChannel",
    "ChargeParty",
    "PriceVariable",
    "PayerInfo",
    "Environment",
    
    # Models
    "CreateBillInput",
    "BillResponse",
    "CallbackData",
    "TransactionData",
    "PaymentRecord",
    "APIResponse",
    "InitPaymentInput",
    "CategoryInput",
    
    # Exceptions
    "ToyyibPayError",
    "ConfigurationError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "InvalidRequestError",
    "PaymentError",
    "WebhookError",
    "SignatureVerificationError",
    "DatabaseError",
    
    # Webhooks
    "WebhookHandler",
    "create_webhook_response",
    
    # Utils
    "utils",
    
    # Version
    "__version__",
]