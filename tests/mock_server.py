"""Mock ToyyibPay server for testing."""

import json
import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import parse_qs

from flask import Flask, request, jsonify
import pytest
from werkzeug.serving import make_server

import toyyibpay
from toyyibpay.enums import PaymentStatus
from tests.factories import CallbackDataFactory, TransactionDataFactory


class MockToyyibPayServer:
    """Mock ToyyibPay server for testing."""
    
    def __init__(self, port: int = 5555):
        self.port = port
        self.app = Flask(__name__)
        self.server = None
        self.thread = None
        
        # Storage
        self.bills: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, List[Dict[str, Any]]] = {}
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.callbacks_sent: List[Dict[str, Any]] = []
        
        # Configuration
        self.delay_range = (0.01, 0.05)  # Response delay range
        self.error_rate = 0.0  # Percentage of requests that should error
        self.valid_api_keys = ["test-api-key", "test-key-12345"]
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup mock API routes."""
        
        @self.app.before_request
        def check_auth():
            """Check API key authentication."""
            if request.path == "/health":
                return None
            
            # Get API key from form data or JSON
            api_key = None
            if request.form:
                api_key = request.form.get("userSecretKey")
            elif request.json:
                api_key = request.json.get("userSecretKey")
            
            if not api_key or api_key not in self.valid_api_keys:
                return jsonify({"error": "Invalid API key"}), 401
        
        @self.app.before_request
        def simulate_delay():
            """Simulate network delay."""
            if request.path != "/health":
                delay = random.uniform(*self.delay_range)
                time.sleep(delay)
        
        @self.app.before_request
        def simulate_errors():
            """Simulate random errors."""
            if request.path != "/health" and random.random() < self.error_rate:
                return jsonify({"error": "Internal server error"}), 500
        
        @self.app.route("/health")
        def health():
            return jsonify({"status": "healthy", "mock": True})
        
        @self.app.route("/index.php/api/createBill", methods=["POST"])
        def create_bill():
            """Mock create bill endpoint."""
            data = request.form.to_dict() if request.form else request.json
            
            # Validate required fields
            required = [
                "categoryCode", "billName", "billDescription",
                "billAmount", "billTo", "billEmail", "billPhone"
            ]
            for field in required:
                if field not in data:
                    return jsonify({"error": f"Missing {field}"}), 400
            
            # Generate bill code
            bill_code = self._generate_bill_code()
            
            # Store bill
            self.bills[bill_code] = {
                **data,
                "billCode": bill_code,
                "createdAt": datetime.now().isoformat(),
                "status": PaymentStatus.PENDING,
            }
            
            # Initialize empty transactions
            self.transactions[bill_code] = []
            
            return jsonify([{"BillCode": bill_code}])
        
        @self.app.route("/index.php/api/getBillTransactions", methods=["POST"])
        def get_bill_transactions():
            """Mock get bill transactions endpoint."""
            data = request.form.to_dict() if request.form else request.json
            
            bill_code = data.get("billCode")
            if not bill_code:
                return jsonify({"error": "Missing billCode"}), 400
            
            if bill_code not in self.bills:
                return jsonify([])  # Empty array for non-existent bill
            
            # Get transactions
            transactions = self.transactions.get(bill_code, [])
            
            # Filter by status if provided
            if "billpaymentStatus" in data:
                status = int(data["billpaymentStatus"])
                transactions = [
                    t for t in transactions
                    if int(t.get("billpaymentStatus", 0)) == status
                ]
            
            return jsonify(transactions)
        
        @self.app.route("/index.php/api/createCategory", methods=["POST"])
        def create_category():
            """Mock create category endpoint."""
            data = request.form.to_dict() if request.form else request.json
            
            if "catname" not in data or "catdescription" not in data:
                return jsonify({"error": "Missing required fields"}), 400
            
            category_code = f"CAT{random.randint(10000, 99999)}"
            
            self.categories[category_code] = {
                "categoryCode": category_code,
                "categoryName": data["catname"],
                "categoryDescription": data["catdescription"],
                "createdAt": datetime.now().isoformat(),
            }
            
            return jsonify({"CategoryCode": category_code})
        
        # Admin endpoints for testing
        @self.app.route("/mock/admin/simulate-payment", methods=["POST"])
        def simulate_payment():
            """Simulate a payment for testing."""
            data = request.json
            bill_code = data.get("billCode")
            status = data.get("status", 1)
            
            if bill_code not in self.bills:
                return jsonify({"error": "Bill not found"}), 404
            
            # Create transaction
            transaction = TransactionDataFactory.create()
            transaction["billcode"] = bill_code
            transaction["billpaymentStatus"] = str(status)
            transaction["billExternalReferenceNo"] = self.bills[bill_code].get(
                "billExternalReferenceNo"
            )
            
            self.transactions[bill_code].append(transaction)
            
            # Send callback if URL provided
            callback_url = self.bills[bill_code].get("billCallbackUrl")
            if callback_url and status in [1, 3]:  # Success or failed
                self._send_callback(bill_code, status)
            
            return jsonify({"success": True, "transaction": transaction})
        
        @self.app.route("/mock/admin/stats", methods=["GET"])
        def get_stats():
            """Get mock server statistics."""
            return jsonify({
                "bills": len(self.bills),
                "transactions": sum(len(t) for t in self.transactions.values()),
                "categories": len(self.categories),
                "callbacks_sent": len(self.callbacks_sent),
                "config": {
                    "error_rate": self.error_rate,
                    "delay_range": self.delay_range,
                }
            })
        
        @self.app.route("/mock/admin/reset", methods=["POST"])
        def reset():
            """Reset mock server state."""
            self.bills.clear()
            self.transactions.clear()
            self.categories.clear()
            self.callbacks_sent.clear()
            return jsonify({"success": True})
        
        @self.app.route("/mock/admin/config", methods=["POST"])
        def update_config():
            """Update mock server configuration."""
            data = request.json
            
            if "error_rate" in data:
                self.error_rate = float(data["error_rate"])
            if "delay_range" in data:
                self.delay_range = tuple(data["delay_range"])
            if "valid_api_keys" in data:
                self.valid_api_keys = data["valid_api_keys"]
            
            return jsonify({"success": True, "config": {
                "error_rate": self.error_rate,
                "delay_range": self.delay_range,
                "valid_api_keys": self.valid_api_keys,
            }})
    
    def _generate_bill_code(self) -> str:
        """Generate unique bill code."""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        while True:
            code = "".join(random.choices(chars, k=8))
            if code not in self.bills:
                return code
    
    def _send_callback(self, bill_code: str, status: int):
        """Send callback to callback URL."""
        import requests
        
        bill = self.bills[bill_code]
        callback_url = bill.get("billCallbackUrl")
        
        if not callback_url:
            return
        
        # Create callback data
        callback_data = CallbackDataFactory.create()
        callback_data.update({
            "billcode": bill_code,
            "order_id": bill.get("billExternalReferenceNo"),
            "status": status,
            "amount": int(float(bill.get("billAmount", 0))),
        })
        
        # Record callback
        self.callbacks_sent.append({
            "url": callback_url,
            "data": callback_data,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Send callback (ignore errors in mock)
        try:
            requests.post(callback_url, data=callback_data, timeout=5)
        except:
            pass
    
    def start(self):
        """Start mock server."""
        self.server = make_server("127.0.0.1", self.port, self.app)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for server to start
        time.sleep(0.5)
        print(f"Mock ToyyibPay server started on port {self.port}")
    
    def stop(self):
        """Stop mock server."""
        if self.server:
            self.server.shutdown()
            self.thread.join()
            print("Mock ToyyibPay server stopped")
    
    def get_bill(self, bill_code: str) -> Optional[Dict[str, Any]]:
        """Get bill by code."""
        return self.bills.get(bill_code)
    
    def get_transactions(self, bill_code: str) -> List[Dict[str, Any]]:
        """Get transactions for a bill."""
        return self.transactions.get(bill_code, [])
    
    def add_transaction(self, bill_code: str, transaction: Dict[str, Any]):
        """Add transaction to a bill."""
        if bill_code in self.transactions:
            self.transactions[bill_code].append(transaction)


# Pytest fixtures
@pytest.fixture(scope="session")
def mock_server():
    """Create and start mock server for entire test session."""
    server = MockToyyibPayServer()
    server.start()
    
    yield server
    
    server.stop()


@pytest.fixture
def clean_mock_server(mock_server):
    """Clean mock server state before each test."""
    import requests
    
    # Reset server state
    requests.post(f"http://127.0.0.1:{mock_server.port}/mock/admin/reset")
    
    # Reset configuration
    requests.post(
        f"http://127.0.0.1:{mock_server.port}/mock/admin/config",
        json={
            "error_rate": 0.0,
            "delay_range": [0.01, 0.05],
        }
    )
    
    return mock_server


# Example usage in tests
class TestWithMockServer:
    """Example tests using mock server."""
    
    def test_create_bill_with_mock(self, clean_mock_server):
        """Test creating bill with mock server."""
        import requests
        
        # Configure client to use mock server
        client = toyyibpay.Client(
            api_key="test-api-key",
            dev_base_url=f"http://127.0.0.1:{clean_mock_server.port}",
            environment="dev",
        )
        
        # Create bill
        bill = client.create_bill(
            name="Test User",
            email="test@example.com",
            phone="0123456789",
            amount=100.00,
            order_id="MOCK-001",
        )
        
        assert bill.bill_code is not None
        
        # Verify bill was stored in mock
        stored_bill = clean_mock_server.get_bill(bill.bill_code)
        assert stored_bill is not None
        assert stored_bill["billExternalReferenceNo"] == "MOCK-001"
    
    def test_payment_flow_with_mock(self, clean_mock_server):
        """Test complete payment flow with mock server."""
        import requests
        
        client = toyyibpay.Client(
            api_key="test-api-key",
            dev_base_url=f"http://127.0.0.1:{clean_mock_server.port}",
            environment="dev",
        )
        
        # Create bill
        bill = client.create_bill(
            name="Test User",
            email="test@example.com",
            phone="0123456789",
            amount=100.00,
            order_id="FLOW-001",
        )
        
        # Simulate successful payment
        requests.post(
            f"http://127.0.0.1:{clean_mock_server.port}/mock/admin/simulate-payment",
            json={
                "billCode": bill.bill_code,
                "status": 1,  # Success
            }
        )
        
        # Check payment status
        status = client.check_payment_status(bill.bill_code)
        assert status == PaymentStatus.SUCCESS
        
        # Verify transaction was recorded
        transactions = clean_mock_server.get_transactions(bill.bill_code)
        assert len(transactions) == 1
        assert transactions[0]["billpaymentStatus"] == "1"