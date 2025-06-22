"""Flask integration example for ToyyibPay SDK."""

import os
from decimal import Decimal
from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import toyyibpay
from toyyibpay.models import CallbackData
from toyyibpay.webhooks.handler import WebhookHandler, create_webhook_response
from toyyibpay.enums import PaymentStatus

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'da-secret-key!!')

# Get database URL and fix postgres:// to postgresql:// for SQLAlchemy 2.0+
database_url = os.getenv(
    'DATABASE_URL',
    'postgresql://user:pass@localhost:port/db_name'
)

if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Configure ToyyibPay
toyyibpay_client = toyyibpay.Client(
    api_key=os.getenv('TOYYIBPAY_API_KEY'),
    environment='production' if os.getenv('FLASK_ENV') == 'production' else 'dev',
    category_id=os.getenv('TOYYIBPAY_CATEGORY_ID'),
)

# Initialize webhook handler
webhook_handler = WebhookHandler()


# Database Models
class Payment(db.Model):
    """Payment record model."""
    __tablename__ = 'payments'
    
    id = db.Column(db.String(50), primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    bill_code = db.Column(db.String(12), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Integer, default=PaymentStatus.PENDING)
    customer_name = db.Column(db.String(255))
    customer_email = db.Column(db.String(255))
    customer_phone = db.Column(db.String(20))
    transaction_ref = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())


# Create tables
with app.app_context():
    db.create_all()


# Routes
@app.route('/api/payments/create', methods=['POST'])
def create_payment():
    """Create a new payment."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Generate order ID if not provided
        order_id = data.get('order_id') or toyyibpay.utils.generate_order_id()
        
        # Create bill with ToyyibPay
        bill = toyyibpay_client.create_bill(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            amount=Decimal(str(data['amount'])),
            order_id=order_id,
            description=data.get('description', 'Payment'),
            return_url=url_for('payment_return', _external=True),
            callback_url=url_for('webhook_callback', _external=True),
        )
        
        # Store payment record
        payment = Payment(
            id=toyyibpay.utils.generate_ulid(),
            order_id=order_id,
            bill_code=bill.bill_code,
            amount=Decimal(str(data['amount'])),
            customer_name=data['name'],
            customer_email=data['email'],
            customer_phone=data['phone'],
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'payment_url': bill.payment_url,
            'bill_code': bill.bill_code,
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/payments/<order_id>/status', methods=['GET'])
def get_payment_status(order_id):
    """Get payment status."""
    payment = Payment.query.filter_by(order_id=order_id).first()
    
    if not payment:
        return jsonify({
            'success': False,
            'error': 'Payment not found'
        }), 404
    
    # Check status with ToyyibPay
    try:
        status = toyyibpay_client.check_payment_status(payment.bill_code)
        
        # Update database if status changed
        if status and status != payment.status:
            payment.status = status
            db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'status': PaymentStatus(payment.status).name,
            'amount': float(payment.amount),
            'bill_code': payment.bill_code,
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/webhooks/toyyibpay', methods=['POST'])
def webhook_callback():
    """Handle ToyyibPay webhook callback."""
    try:
        # Get request data
        data = request.form.to_dict() if request.form else request.get_json()
        headers = dict(request.headers)
        
        # Process webhook
        callback_data = webhook_handler.process(data, headers)
        
        # Update payment status
        payment = Payment.query.filter_by(bill_code=callback_data.bill_code).first()
        if payment:
            payment.status = callback_data.status
            payment.transaction_ref = callback_data.ref_no
            db.session.commit()
            
            # Trigger any post-payment processing
            if callback_data.status == PaymentStatus.SUCCESS:
                process_successful_payment(payment, callback_data)
            elif callback_data.status == PaymentStatus.FAILED:
                process_failed_payment(payment, callback_data)
        
        return jsonify(create_webhook_response(success=True))
        
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        return jsonify(create_webhook_response(success=False, message=str(e))), 200


@app.route('/payment/return')
def payment_return():
    """Handle payment return URL."""
    # Get parameters from query string
    status_id = request.args.get('status_id', type=int)
    billcode = request.args.get('billcode')
    order_id = request.args.get('order_id')
    
    # Map status
    status_map = {1: 'success', 2: 'pending', 3: 'failed'}
    status = status_map.get(status_id, 'unknown')
    
    # You can render a template or redirect to your frontend
    return f"""
    <html>
        <body>
            <h1>Payment {status.title()}</h1>
            <p>Order ID: {order_id}</p>
            <p>Bill Code: {billcode}</p>
            <a href="/">Return to Home</a>
        </body>
    </html>
    """


# Helper functions
def process_successful_payment(payment, callback_data):
    """Process successful payment."""
    app.logger.info(f"Payment successful: {payment.order_id}")
    # Add your business logic here:
    # - Send confirmation email
    # - Update inventory
    # - Activate subscription
    # - etc.


def process_failed_payment(payment, callback_data):
    """Process failed payment."""
    app.logger.info(f"Payment failed: {payment.order_id} - Reason: {callback_data.reason}")
    # Add your business logic here:
    # - Send failure notification
    # - Log for retry
    # - etc.


# Register webhook handlers
@webhook_handler.on_payment_success
def on_payment_success(data: CallbackData):
    """Handle successful payment webhook."""
    app.logger.info(f"Webhook: Payment successful for {data.order_id}")


@webhook_handler.on_payment_failed
def on_payment_failed(data: CallbackData):
    """Handle failed payment webhook."""
    app.logger.warning(f"Webhook: Payment failed for {data.order_id}")


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# Health check
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'toyyibpay-flask-integration'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)