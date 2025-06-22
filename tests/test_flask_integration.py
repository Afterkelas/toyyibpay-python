"""Integration tests for Flask application."""

import json
from decimal import Decimal
from unittest.mock import patch, Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient

from toyyibpay import Client, PaymentStatus
from toyyibpay.webhooks import WebhookHandler
from tests.factories import (
    create_test_bill,
    create_test_webhook,
    create_test_config,
    CallbackDataFactory,
)


@pytest.fixture
def flask_app():
    """Create Flask application for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    
    # Initialize ToyyibPay client
    client = Client(api_key="test-api-key")
    webhook_handler = WebhookHandler()
    
    # Store in app context
    app.toyyibpay_client = client
    app.webhook_handler = webhook_handler
    
    # Define routes
    @app.route("/create-payment", methods=["POST"])
    def create_payment():
        data = request.get_json()
        
        try:
            bill = app.toyyibpay_client.create_bill(
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                amount=Decimal(str(data["amount"])),
                order_id=data.get("order_id", ""),
                description=data.get("description", "Payment"),
            )
            
            return jsonify({
                "success": True,
                "payment_url": bill.payment_url,
                "bill_code": bill.bill_code,
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
    
    @app.route("/payment-status/<order_id>", methods=["GET"])
    def payment_status(order_id):
        # Mock implementation
        return jsonify({
            "success": True,
            "order_id": order_id,
            "status": "pending",
            "amount": "100.00",
        })
    
    @app.route("/webhooks/toyyibpay", methods=["POST"])
    def webhook_callback():
        try:
            data = request.form.to_dict() if request.form else request.get_json()
            callback_data = app.webhook_handler.process(data)
            
            return jsonify({
                "success": True,
                "message": "Webhook processed",
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 200  # Return 200 to acknowledge receipt
    
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "service": "toyyibpay-flask"
        })
    
    # Import here to avoid circular import
    from flask import request, jsonify
    
    return app


@pytest.fixture
def flask_client(flask_app) -> FlaskClient:
    """Create Flask test client."""
    return flask_app.test_client()


@pytest.mark.integration
class TestFlaskIntegration:
    """Test Flask integration."""
    
    def test_health_check(self, flask_client):
        """Test health check endpoint."""
        response = flask_client.get("/health")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
    
    @patch("toyyibpay.client.ToyyibPayClient.create_bill")
    def test_create_payment_success(self, mock_create_bill, flask_client):
        """Test successful payment creation."""
        # Mock response
        mock_bill = Mock()
        mock_bill.payment_url = "https://toyyibpay.com/ABC123"
        mock_bill.bill_code = "ABC123"
        mock_create_bill.return_value = mock_bill
        
        # Make request
        payment_data = create_test_bill()
        response = flask_client.post(
            "/create-payment",
            json=payment_data,
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["payment_url"] == "https://toyyibpay.com/ABC123"
        assert data["bill_code"] == "ABC123"
        
        # Verify client was called
        mock_create_bill.assert_called_once()
    
    @patch("toyyibpay.client.ToyyibPayClient.create_bill")
    def test_create_payment_validation_error(self, mock_create_bill, flask_client):
        """Test payment creation with validation error."""
        # Mock validation error
        mock_create_bill.side_effect = ValueError("Amount must be greater than 0")
        
        # Make request with invalid data
        payment_data = create_test_bill(amount=-10)
        response = flask_client.post(
            "/create-payment",
            json=payment_data,
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "Amount must be greater than 0" in data["error"]
    
    def test_create_payment_missing_fields(self, flask_client):
        """Test payment creation with missing fields."""
        response = flask_client.post(
            "/create-payment",
            json={"name": "Test User"},  # Missing required fields
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
    
    def test_payment_status_endpoint(self, flask_client):
        """Test payment status endpoint."""
        response = flask_client.get("/payment-status/ORD-12345")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["order_id"] == "ORD-12345"
        assert data["status"] == "pending"
    
    def test_webhook_callback_form_data(self, flask_client, flask_app):
        """Test webhook callback with form data."""
        # Register webhook handler
        handler_called = False
        
        @flask_app.webhook_handler.on_payment_success
        def on_success(data):
            nonlocal handler_called
            handler_called = True
        
        # Send webhook
        webhook_data = CallbackDataFactory.create(status=1)
        response = flask_client.post(
            "/webhooks/toyyibpay",
            data=webhook_data,
            content_type="application/x-www-form-urlencoded"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert handler_called
    
    def test_webhook_callback_json(self, flask_client):
        """Test webhook callback with JSON data."""
        webhook_data = CallbackDataFactory.create(status=1)
        response = flask_client.post(
            "/webhooks/toyyibpay",
            json=webhook_data,
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_webhook_callback_error(self, flask_client):
        """Test webhook callback with invalid data."""
        response = flask_client.post(
            "/webhooks/toyyibpay",
            json={"invalid": "data"},
            content_type="application/json"
        )
        
        # Should return 200 to acknowledge receipt even on error
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data


@pytest.mark.integration
class TestFlaskMiddleware:
    """Test Flask middleware and request handling."""
    
    def test_content_type_handling(self, flask_client):
        """Test different content types."""
        payment_data = create_test_bill()
        
        # Test JSON
        response = flask_client.post(
            "/create-payment",
            data=json.dumps(payment_data),
            content_type="application/json"
        )
        assert response.status_code in [200, 400]
        
        # Test form data (should fail for create-payment)
        response = flask_client.post(
            "/create-payment",
            data=payment_data,
            content_type="application/x-www-form-urlencoded"
        )
        assert response.status_code == 400
    
    def test_cors_headers(self, flask_app):
        """Test CORS headers if configured."""
        # Add CORS to app
        @flask_app.after_request
        def after_request(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response
        
        client = flask_app.test_client()
        response = client.get("/health")
        
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
    
    def test_error_handling(self, flask_app):
        """Test error handling."""
        @flask_app.route("/error-test")
        def error_test():
            raise Exception("Test error")
        
        @flask_app.errorhandler(Exception)
        def handle_error(e):
            from flask import jsonify
            return jsonify({"error": str(e)}), 500
        
        client = flask_app.test_client()
        response = client.get("/error-test")
        
        assert response.status_code == 500
        assert "Test error" in response.get_json()["error"]


@pytest.mark.integration
class TestFlaskDatabase:
    """Test Flask with database integration."""
    
    @pytest.fixture
    def flask_app_with_db(self, flask_app, db_engine):
        """Add database to Flask app."""
        from toyyibpay.db.postgres import PostgresPaymentStore
        
        flask_app.payment_store = PostgresPaymentStore(db_engine)
        flask_app.payment_store.create_tables()
        
        return flask_app
    
    def test_payment_persistence(self, flask_app_with_db):
        """Test payment data persistence."""
        client = flask_app_with_db.test_client()
        
        # Add route for testing
        @flask_app_with_db.route("/test-db", methods=["POST"])
        def test_db():
            from flask import request, jsonify
            data = request.get_json()
            
            with flask_app_with_db.payment_store.session() as session:
                payment = flask_app_with_db.payment_store.create_payment(
                    session,
                    order_id=data["order_id"],
                    amount=Decimal(str(data["amount"])),
                    bill_code="TEST123",
                )
                return jsonify({"payment_id": payment.id})
        
        # Test creation
        response = client.post(
            "/test-db",
            json={"order_id": "ORD-TEST", "amount": "100.00"}
        )
        
        assert response.status_code == 200
        payment_id = response.get_json()["payment_id"]
        assert payment_id is not None