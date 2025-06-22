"""FastAPI integration example for ToyyibPay SDK."""

from decimal import Decimal
from typing import Optional
import os

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
import toyyibpay
from toyyibpay.models import CallbackData, InitPaymentInput
from toyyibpay.webhooks.handler import WebhookHandler, create_webhook_response
from toyyibpay.db.postgres import PostgresPaymentStore
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Initialize FastAPI app
app = FastAPI(title="ToyyibPay Integration Example")

# Configure ToyyibPay
toyyibpay_config = toyyibpay.ToyyibPayConfig.from_env()
toyyibpay_client = toyyibpay.Client(config=toyyibpay_config)

# Initialize database (optional)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/toyyibpay")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize payment store
payment_store = PostgresPaymentStore(engine)
payment_store.create_tables()

# Initialize webhook handler
webhook_handler = WebhookHandler()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request models
class CreatePaymentRequest(BaseModel):
    """Request model for creating payment."""
    name: str
    email: EmailStr
    phone: str
    amount: Decimal
    order_id: Optional[str] = None
    description: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response model for payment status."""
    order_id: str
    status: str
    amount: Decimal
    payment_url: Optional[str] = None


# API Routes
@app.post("/api/payments/create", response_model=PaymentStatusResponse)
async def create_payment(
    request: CreatePaymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new payment."""
    try:
        # Generate order ID if not provided
        order_id = request.order_id or toyyibpay.utils.generate_order_id()
        
        # Create bill with ToyyibPay
        bill = toyyibpay_client.create_bill(
            name=request.name,
            email=request.email,
            phone=request.phone,
            amount=request.amount,
            order_id=order_id,
            description=request.description,
            return_url=f"https://yourdomain.com/payment/return/{order_id}",
            callback_url="https://yourdomain.com/webhooks/toyyibpay",
        )
        
        # Store payment record in database
        payment_record = payment_store.create_payment(
            db,
            order_id=order_id,
            amount=request.amount,
            bill_code=bill.bill_code,
            customer_name=request.name,
            customer_email=request.email,
            customer_phone=request.phone,
        )
        
        # You can add background tasks here
        background_tasks.add_task(
            log_payment_creation,
            order_id=order_id,
            amount=request.amount
        )
        
        return PaymentStatusResponse(
            order_id=order_id,
            status="pending",
            amount=request.amount,
            payment_url=bill.payment_url,
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/payments/{order_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(order_id: str, db: Session = Depends(get_db)):
    """Get payment status."""
    # Get payment from database
    payment = payment_store.get_payment_by_order_id(db, order_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Check status with ToyyibPay
    status = toyyibpay_client.check_payment_status(payment.bill_code)
    
    # Update database if status changed
    if status and status != payment.status:
        payment_store.update_payment_status(db, payment.id, status)
    
    return PaymentStatusResponse(
        order_id=order_id,
        status=status.name if status else payment.status.name,
        amount=payment.amount,
    )


@app.post("/webhooks/toyyibpay")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle ToyyibPay webhook callback."""
    try:
        # Get request body
        body = await request.body()
        headers = dict(request.headers)
        
        # Process webhook
        callback_data = webhook_handler.process(body, headers)
        
        # Update payment status in database
        payment = payment_store.get_payment_by_bill_code(db, callback_data.bill_code)
        if payment:
            payment_store.update_payment_status(
                db,
                payment.id,
                callback_data.status,
                transaction_ref=callback_data.ref_no,
                transaction_time=callback_data.transaction_time,
            )
            
            # Add background task for post-payment processing
            background_tasks.add_task(
                process_payment_webhook,
                callback_data=callback_data,
                payment=payment
            )
        
        return create_webhook_response(success=True)
        
    except Exception as e:
        return create_webhook_response(success=False, message=str(e))


@app.get("/payment/return/{order_id}")
async def payment_return(order_id: str, status_id: int, billcode: str):
    """Handle payment return URL."""
    # Map ToyyibPay status to readable status
    status_map = {1: "success", 2: "pending", 3: "failed"}
    status = status_map.get(status_id, "unknown")
    
    # Redirect to your frontend with status
    return RedirectResponse(
        url=f"https://yourfrontend.com/payment-complete?order_id={order_id}&status={status}"
    )


# Background tasks
async def log_payment_creation(order_id: str, amount: Decimal):
    """Log payment creation (example background task)."""
    print(f"Payment created: {order_id} for amount {amount}")


async def process_payment_webhook(callback_data: CallbackData, payment):
    """Process payment webhook (example background task)."""
    if callback_data.status == toyyibpay.PaymentStatus.SUCCESS:
        # Send confirmation email
        print(f"Sending confirmation email for order {payment.order_id}")
        # Update inventory
        print(f"Updating inventory for order {payment.order_id}")
        # Notify other services
        print(f"Notifying services about successful payment {payment.order_id}")


# Register webhook handlers
@webhook_handler.on_payment_success
def on_payment_success(data: CallbackData):
    """Handle successful payment."""
    print(f"Payment successful: {data.order_id}")


@webhook_handler.on_payment_failed
def on_payment_failed(data: CallbackData):
    """Handle failed payment."""
    print(f"Payment failed: {data.order_id} - Reason: {data.reason}")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "toyyibpay-integration"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)