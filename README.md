# ToyyibPay Python SDK

A modern, easy-to-use Python SDK for integrating with ToyyibPay payment gateway. Inspired by Stripe's SDK design principles.

## Features

- 🚀 Simple, intuitive API
- 🔒 Full type hints support
- ⚡ Async/await support
- 🛡️ Comprehensive error handling
- 🔧 Easy integration with Flask and FastAPI
- 📊 Built-in webhook handling
- 🗄️ Optional database integration (PostgreSQL first, MySQL/MongoDB coming soon)
- 🧪 Well-tested ~~and production-ready~~ (nvm not production-ready yet till v1.0.0)

## Installation

```bash
pip install toyyibpay
```

### With specific integrations:

```bash
# For PostgreSQL support
pip install toyyibpay[postgres]

# For Flask integration
pip install toyyibpay[flask]

# For FastAPI integration
pip install toyyibpay[fastapi]

# For everything
pip install toyyibpay[all]
```

### Development Installation

For development with tests and documentation:

```bash
# Clone the repository
git clone https://github.com/waizwafiq/toyyibpay-python.git
cd toyyibpay-python

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```python
import toyyibpay

# Initialize client
client = toyyibpay.Client(api_key="your-api-key")

# Create a payment
bill = client.create_bill(
    name="John Doe",
    email="john@example.com",
    phone="0123456789",
    amount=100.00,  # MYR 100.00
    order_id="ORD-12345",
    description="Purchase of Product X"
)

print(f"Payment URL: {bill.payment_url}")
print(f"Bill Code: {bill.bill_code}")
```

### Async Usage

```python
import asyncio
import toyyibpay

async def create_payment():
    async with toyyibpay.AsyncClient(api_key="your-api-key") as client:
        bill = await client.create_bill(
            name="John Doe",
            email="john@example.com",
            phone="0123456789",
            amount=100.00,
            order_id="ORD-12345"
        )
        return bill

# Run async function
bill = asyncio.run(create_payment())
```

### Environment-based Configuration

```python
import os
import toyyibpay

# Set environment variables
os.environ['TOYYIBPAY_API_KEY'] = 'your-api-key'
os.environ['TOYYIBPAY_CATEGORY_ID'] = 'your-category-id'
os.environ['TOYYIBPAY_ENVIRONMENT'] = 'production'  # or 'dev'

# Create client from environment
config = toyyibpay.ToyyibPayConfig.from_env()
client = toyyibpay.Client(config=config)
```

## Flask Integration

```python
from flask import Flask, request, jsonify
import toyyibpay

app = Flask(__name__)
client = toyyibpay.Client(api_key="your-api-key")

@app.route('/create-payment', methods=['POST'])
def create_payment():
    data = request.get_json()
    
    try:
        bill = client.create_bill(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            amount=data['amount'],
            order_id=data.get('order_id')
        )
        
        return jsonify({
            'success': True,
            'payment_url': bill.payment_url,
            'bill_code': bill.bill_code
        })
    except toyyibpay.ToyyibPayError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
```

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import toyyibpay

app = FastAPI()
client = toyyibpay.Client(api_key="your-api-key")

class PaymentRequest(BaseModel):
    name: str
    email: str
    phone: str
    amount: float

@app.post("/create-payment")
async def create_payment(payment: PaymentRequest):
    try:
        bill = client.create_bill(
            name=payment.name,
            email=payment.email,
            phone=payment.phone,
            amount=payment.amount,
            order_id=toyyibpay.utils.generate_order_id()
        )
        
        return {
            "payment_url": bill.payment_url,
            "bill_code": bill.bill_code
        }
    except toyyibpay.ToyyibPayError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Webhook Handling

```python
import toyyibpay
from toyyibpay.webhooks import WebhookHandler

# Create webhook handler
webhook_handler = WebhookHandler()

# Register event handlers
@webhook_handler.on_payment_success
def handle_success(data: toyyibpay.CallbackData):
    print(f"Payment {data.order_id} successful!")
    # Update order status, send email, etc.

@webhook_handler.on_payment_failed
def handle_failure(data: toyyibpay.CallbackData):
    print(f"Payment {data.order_id} failed: {data.reason}")
    # Handle failed payment

# Process webhook (in your webhook endpoint)
def process_webhook(request_body, headers):
    try:
        callback_data = webhook_handler.process(request_body, headers)
        return {"success": True}
    except toyyibpay.WebhookError as e:
        return {"success": False, "error": str(e)}
```

## Database Integration Sample Code (Optional)

```python
from sqlalchemy import create_engine
import toyyibpay
from toyyibpay.db import PostgresPaymentStore

# Setup database
engine = create_engine("postgresql://user:pass@localhost/mydb")
payment_store = PostgresPaymentStore(engine)
payment_store.create_tables()

# Create payment with database tracking
def create_payment_with_tracking(customer_data):
    # Create bill with ToyyibPay
    bill = client.create_bill(**customer_data)
    
    # Store in database
    with payment_store.session() as session:
        payment = payment_store.create_payment(
            session,
            order_id=customer_data['order_id'],
            amount=customer_data['amount'],
            bill_code=bill.bill_code,
            customer_name=customer_data['name'],
            customer_email=customer_data['email']
        )
    
    return bill
```

## API Reference

### Client Methods

#### `create_bill()`
Create a new payment bill.

```python
bill = client.create_bill(
    name="Waiz Wafiq",           # Customer name (required)
    email="waiz@gmail.com",      # Customer email (required)
    phone="0123456789",          # Customer phone (required)
    amount=100.00,               # Amount in MYR (required)
    order_id="ORD-12345",        # Your reference ID (required)
    description="bayar hutang",  # Description (optional)
    return_url="https://...",    # Return URL (optional)
    callback_url="https://...",  # Callback URL (optional)
)
```

#### `get_bill_transactions()`
Get transaction history for a bill.

```python
# Get all transactions
transactions = client.get_bill_transactions("bill_code")

# Get only successful transactions
successful = client.get_bill_transactions(
    "bill_code", 
    status=toyyibpay.PaymentStatus.SUCCESS
)
```

#### `check_payment_status()`
Check payment status for a bill.

```python
status = client.check_payment_status("bill_code")
if status == toyyibpay.PaymentStatus.SUCCESS:
    print("Payment successful!")
```

#### `create_category()`
Create a new payment category.

```python
category = client.create_category(
    name="Online Store",
    description="Payments for online store"
)
```

### Enums

- `PaymentStatus`: SUCCESS, PENDING, FAILED, PENDING_TRANSACTION
- `PaymentChannel`: FPX, CREDIT_CARD, FPX_AND_CREDIT_CARD
- `Environment`: DEV, STAGING, PRODUCTION

### Exceptions

- `ToyyibPayError`: Base exception
- `AuthenticationError`: Invalid API key
- `ValidationError`: Invalid request data
- `NetworkError`: Network-related errors
- `APIError`: ToyyibPay API errors

## Configuration

### Environment Variables

- `TOYYIBPAY_API_KEY`: Your ToyyibPay API key
- `TOYYIBPAY_CATEGORY_ID`: Default category ID
- `TOYYIBPAY_ENVIRONMENT`: Environment (dev/staging/production)
- `TOYYIBPAY_RETURN_URL`: Default return URL
- `TOYYIBPAY_CALLBACK_URL`: Default callback URL
- `DATABASE_URL`: PostgreSQL connection string (optional)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=toyyibpay
```

### Code Style

```bash
# Format code
black toyyibpay tests

# Sort imports
isort toyyibpay tests

# Type checking
mypy toyyibpay
```

## Testing

Tests are not included in the PyPI package but are available in the [GitHub repository](https://github.com/mwaizwafiq/toyyibpay-python).

### Running Tests from Source

```bash
# Clone the repository
git clone https://github.com/mwaizwafiq/toyyibpay-python.git
cd toyyibpay-python

# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=toyyibpay
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. **Write tests for your changes**
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request


## Acknowledgments

- Inspired by Stripe's excellent Python SDK
- Thanks to the ToyyibPay team for their payment gateway service