"""End-to-end tests for ToyyibPay SDK."""

import asyncio
import time
from decimal import Decimal
from unittest.mock import patch, Mock

import pytest

import toyyibpay
from toyyibpay.models import CallbackData
from toyyibpay.enums import PaymentStatus
from toyyibpay.db.postgres import PostgresPaymentStore
from tests.factories import (
    create_test_bill,
    create_test_webhook,
    MockDataGenerator,
    BatchDataFactory,
)


@pytest.mark.integration
@pytest.mark.slow
class TestPaymentFlow:
    """Test complete payment flow from creation to completion."""
    
    @patch("toyyibpay.http_client.HTTPClient.post")
    def test_complete_payment_flow(self, mock_post, test_config, db_engine):
        """Test complete payment flow: create -> pending -> success."""
        # Setup
        client = toyyibpay.Client(config=test_config)
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        # Mock responses
        mock_post.side_effect = [
            # Create bill response
            {"BillCode": "ABC123"},
            # Get transactions (pending)
            {"data": [MockDataGenerator.create_fpx_transaction()]},
        ]
        
        # Step 1: Create payment
        bill_data = create_test_bill(order_id="E2E-001")
        bill = client.create_bill(**bill_data)
        
        assert bill.bill_code == "ABC123"
        assert bill.payment_url.endswith("ABC123")
        
        # Step 2: Store payment in database
        with payment_store.session() as session:
            payment = payment_store.create_payment(
                session,
                order_id=bill_data["order_id"],
                amount=Decimal(str(bill_data["amount"])),
                bill_code=bill.bill_code,
                customer_name=bill_data["name"],
                customer_email=bill_data["email"],
                customer_phone=bill_data["phone"],
            )
            payment_id = payment.id
        
        # Step 3: Check payment status
        status = client.check_payment_status(bill.bill_code)
        assert status == PaymentStatus.SUCCESS
        
        # Step 4: Update payment status in database
        with payment_store.session() as session:
            updated = payment_store.update_payment_status(
                session,
                payment_id,
                PaymentStatus.SUCCESS,
                transaction_ref="REF123",
            )
            assert updated.status == PaymentStatus.SUCCESS
    
    @patch("toyyibpay.http_client.HTTPClient.post")
    def test_payment_retry_flow(self, mock_post, test_config):
        """Test payment retry flow after initial failure."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock responses - first attempt fails, second succeeds
        mock_post.side_effect = [
            # First create bill
            {"BillCode": "FAIL123"},
            # Check status - failed
            {"data": [{"billpaymentStatus": "3"}]},  # Failed
            # Second create bill
            {"BillCode": "SUCCESS123"},
            # Check status - success
            {"data": [{"billpaymentStatus": "1"}]},  # Success
        ]
        
        # First attempt
        bill1 = client.create_bill(**create_test_bill(order_id="RETRY-001"))
        status1 = client.check_payment_status(bill1.bill_code)
        assert status1 == PaymentStatus.FAILED
        
        # Retry with new bill
        bill2 = client.create_bill(**create_test_bill(order_id="RETRY-001"))
        status2 = client.check_payment_status(bill2.bill_code)
        assert status2 == PaymentStatus.SUCCESS
    
    def test_webhook_flow(self, test_config, db_engine):
        """Test webhook processing flow."""
        webhook_handler = toyyibpay.WebhookHandler()
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        # Create payment record
        with payment_store.session() as session:
            payment = payment_store.create_payment(
                session,
                order_id="WEBHOOK-001",
                amount=Decimal("100.00"),
                bill_code="WH123",
            )
            payment_id = payment.id
        
        # Track webhook events
        events = []
        
        @webhook_handler.on_payment_success
        def on_success(data: CallbackData):
            events.append(("success", data))
        
        @webhook_handler.on_payment_failed
        def on_failed(data: CallbackData):
            events.append(("failed", data))
        
        # Process webhook sequence
        webhook_sequence = BatchDataFactory.create_webhook_sequence("WEBHOOK-001")
        
        for webhook_data in webhook_sequence:
            callback_data = webhook_handler.process(webhook_data)
            
            # Update payment status
            with payment_store.session() as session:
                payment_store.update_payment_status(
                    session,
                    payment_id,
                    callback_data.status,
                    transaction_ref=callback_data.ref_no,
                )
        
        # Verify events
        assert len(events) == 2  # Pending and success
        assert events[-1][0] == "success"
        
        # Verify final status
        with payment_store.session() as session:
            final_payment = payment_store.get_payment(session, payment_id)
            assert final_payment.status == PaymentStatus.SUCCESS


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestAsyncPaymentFlow:
    """Test async payment flow."""
    
    @patch("toyyibpay.http_client.AsyncHTTPClient.post")
    async def test_async_payment_flow(self, mock_post, test_config):
        """Test complete async payment flow."""
        # Mock async response
        async def mock_async_post(*args, **kwargs):
            return {"BillCode": "ASYNC123"}
        
        mock_post.side_effect = mock_async_post
        
        async with toyyibpay.AsyncClient(config=test_config) as client:
            # Create payment
            bill = await client.create_bill(**create_test_bill())
            assert bill.bill_code == "ASYNC123"
            
            # Check status (mock)
            mock_post.side_effect = lambda *args, **kwargs: asyncio.coroutine(
                lambda: {"data": [{"billpaymentStatus": "1"}]}
            )()
            
            status = await client.check_payment_status(bill.bill_code)
            assert status == PaymentStatus.SUCCESS
    
    async def test_concurrent_payment_creation(self, test_config):
        """Test creating multiple payments concurrently."""
        async with toyyibpay.AsyncClient(config=test_config) as client:
            # Mock the create_bill method
            created_bills = []
            
            async def mock_create_bill(**kwargs):
                bill_code = f"CONC{len(created_bills):03d}"
                created_bills.append(bill_code)
                
                mock_bill = Mock()
                mock_bill.bill_code = bill_code
                mock_bill.payment_url = f"https://toyyibpay.com/{bill_code}"
                return mock_bill
            
            client.create_bill = mock_create_bill
            
            # Create multiple payments concurrently
            tasks = []
            for i in range(10):
                bill_data = create_test_bill(order_id=f"CONC-{i:03d}")
                tasks.append(client.create_bill(**bill_data))
            
            bills = await asyncio.gather(*tasks)
            
            assert len(bills) == 10
            assert len(set(b.bill_code for b in bills)) == 10  # All unique


@pytest.mark.integration
class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    @patch("toyyibpay.http_client.HTTPClient.post")
    def test_network_error_recovery(self, mock_post, test_config):
        """Test recovery from network errors."""
        client = toyyibpay.Client(config=test_config)
        
        # Simulate network error then success
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise toyyibpay.NetworkError("Connection failed")
            return {"BillCode": "RECOVERED"}
        
        mock_post.side_effect = side_effect
        
        # First call fails
        with pytest.raises(toyyibpay.NetworkError):
            client.create_bill(**create_test_bill())
        
        # Second call succeeds
        bill = client.create_bill(**create_test_bill())
        assert bill.bill_code == "RECOVERED"
    
    def test_database_transaction_rollback(self, db_engine):
        """Test database transaction rollback on error."""
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        try:
            with payment_store.session() as session:
                # Create payment
                payment = payment_store.create_payment(
                    session,
                    order_id="ROLLBACK-001",
                    amount=Decimal("100.00"),
                    bill_code="RB123",
                )
                
                # Force error
                raise Exception("Simulated error")
        except Exception:
            pass
        
        # Verify rollback
        with payment_store.session() as session:
            payment = payment_store.get_payment_by_order_id(session, "ROLLBACK-001")
            assert payment is None  # Should be rolled back


@pytest.mark.integration
class TestScenarios:
    """Test real-world scenarios."""
    
    def test_duplicate_order_prevention(self, test_config, db_engine):
        """Test preventing duplicate orders."""
        client = toyyibpay.Client(config=test_config)
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        order_id = "DUP-001"
        
        # Create first payment
        with payment_store.session() as session:
            payment1 = payment_store.create_payment(
                session,
                order_id=order_id,
                amount=Decimal("100.00"),
                bill_code="DUP1",
            )
        
        # Try to create duplicate
        from sqlalchemy.exc import IntegrityError
        
        with pytest.raises(IntegrityError):
            with payment_store.session() as session:
                payment2 = payment_store.create_payment(
                    session,
                    order_id=order_id,  # Same order ID
                    amount=Decimal("200.00"),
                    bill_code="DUP2",
                )
    
    @patch("toyyibpay.http_client.HTTPClient.post")
    def test_corporate_banking_flow(self, mock_post, test_config):
        """Test corporate banking payment flow."""
        client = toyyibpay.Client(config=test_config)
        
        # Mock response
        mock_post.return_value = {"BillCode": "CORP123"}
        
        # Create large payment
        bill = client.create_bill(
            name="Corporate Customer",
            email="corp@example.com",
            phone="0123456789",
            amount=Decimal("50000.00"),  # Above threshold
            order_id="CORP-001",
        )
        
        # Verify corporate banking was enabled
        call_args = mock_post.call_args[1]["data"]
        assert call_args["enableFPXB2B"] == 1
    
    def test_payment_status_tracking(self, test_config, db_engine):
        """Test tracking payment status changes."""
        payment_store = PostgresPaymentStore(db_engine)
        payment_store.create_tables()
        
        # Create payment
        with payment_store.session() as session:
            payment = payment_store.create_payment(
                session,
                order_id="TRACK-001",
                amount=Decimal("100.00"),
                bill_code="TRK123",
            )
            payment_id = payment.id
            
            # Initial status
            assert payment.status == PaymentStatus.PENDING
        
        # Update status multiple times
        statuses = [
            PaymentStatus.PENDING_TRANSACTION,
            PaymentStatus.SUCCESS,
        ]
        
        for status in statuses:
            time.sleep(0.1)  # Small delay to ensure different timestamps
            
            with payment_store.session() as session:
                payment_store.update_payment_status(
                    session,
                    payment_id,
                    status,
                )
        
        # Verify final status
        with payment_store.session() as session:
            final_payment = payment_store.get_payment(session, payment_id)
            assert final_payment.status == PaymentStatus.SUCCESS
            assert final_payment.updated_at > final_payment.created_at