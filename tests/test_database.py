"""Tests for database integration."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

from toyyibpay.db.postgres import PostgresPaymentStore, PaymentModel, Base
from toyyibpay.enums import PaymentStatus, PaymentChannel


@pytest.mark.db
class TestPostgresPaymentStore:
    """Test PostgreSQL payment store functionality."""
    
    @pytest.mark.unit
    def test_payment_store_initialization(self, db_engine):
        """Test payment store initialization."""
        store = PostgresPaymentStore(db_engine)
        assert store.engine == db_engine
        assert store.SessionLocal is not None
    
    @pytest.mark.unit
    def test_create_tables(self, db_engine):
        """Test creating database tables."""
        store = PostgresPaymentStore(db_engine)
        store.create_tables()
        
        # Tables should exist
        assert "payments" in db_engine.table_names()
    
    @pytest.mark.unit
    def test_drop_tables(self, db_engine):
        """Test dropping database tables."""
        store = PostgresPaymentStore(db_engine)
        store.create_tables()
        store.drop_tables()
        
        # Tables should not exist
        assert "payments" not in db_engine.table_names()
    
    @pytest.mark.unit
    def test_session_context_manager(self, payment_store):
        """Test session context manager."""
        with payment_store.session() as session:
            assert session is not None
            # Session should be active
            assert session.is_active
    
    @pytest.mark.unit
    def test_session_rollback_on_error(self, payment_store):
        """Test session rollback on error."""
        try:
            with payment_store.session() as session:
                # Create invalid payment to trigger error
                payment = PaymentModel(
                    order_id=None,  # This should cause an error
                    amount=100.00,
                    bill_code="ABC123",
                )
                session.add(payment)
                session.flush()
        except Exception:
            pass
        
        # Session should have been rolled back
        with payment_store.session() as session:
            count = session.query(PaymentModel).count()
            assert count == 0


@pytest.mark.db
class TestPaymentModelOperations:
    """Test payment model database operations."""
    
    @pytest.mark.unit
    def test_create_payment(self, payment_store, db_session):
        """Test creating a payment record."""
        payment = payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone="0123456789",
            tp_channel=PaymentChannel.FPX,
            tp_category_code="CAT123",
        )
        
        assert payment.id is not None
        assert payment.order_id == "ORD-12345"
        assert payment.amount == Decimal("100.00")
        assert payment.bill_code == "ABC123"
        assert payment.status == PaymentStatus.PENDING
        assert payment.created_at is not None
    
    @pytest.mark.unit
    def test_create_payment_duplicate_order_id(self, payment_store, db_session):
        """Test creating payment with duplicate order ID fails."""
        # Create first payment
        payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Try to create duplicate
        with pytest.raises(IntegrityError):
            payment_store.create_payment(
                db_session,
                order_id="ORD-12345",  # Duplicate
                amount=Decimal("200.00"),
                bill_code="DEF456",
            )
            db_session.commit()
    
    @pytest.mark.unit
    def test_get_payment_by_id(self, payment_store, db_session):
        """Test getting payment by ID."""
        # Create payment
        created = payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Get payment
        payment = payment_store.get_payment(db_session, created.id)
        assert payment is not None
        assert payment.id == created.id
        assert payment.order_id == "ORD-12345"
    
    @pytest.mark.unit
    def test_get_payment_not_found(self, payment_store, db_session):
        """Test getting non-existent payment returns None."""
        payment = payment_store.get_payment(db_session, "NONEXISTENT")
        assert payment is None
    
    @pytest.mark.unit
    def test_get_payment_by_order_id(self, payment_store, db_session):
        """Test getting payment by order ID."""
        # Create payment
        payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Get payment
        payment = payment_store.get_payment_by_order_id(db_session, "ORD-12345")
        assert payment is not None
        assert payment.order_id == "ORD-12345"
    
    @pytest.mark.unit
    def test_get_payment_by_bill_code(self, payment_store, db_session):
        """Test getting payment by bill code."""
        # Create payment
        payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Get payment
        payment = payment_store.get_payment_by_bill_code(db_session, "ABC123")
        assert payment is not None
        assert payment.bill_code == "ABC123"
    
    @pytest.mark.unit
    def test_update_payment_status(self, payment_store, db_session):
        """Test updating payment status."""
        # Create payment
        created = payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Update status
        updated = payment_store.update_payment_status(
            db_session,
            created.id,
            PaymentStatus.SUCCESS,
            transaction_ref="REF123",
            transaction_message="Payment successful",
            transaction_time="2024-01-15T10:30:00Z",
        )
        db_session.commit()
        
        assert updated is not None
        assert updated.status == PaymentStatus.SUCCESS
        assert updated.tp_transaction_ref == "REF123"
        assert updated.tp_transaction_message == "Payment successful"
        assert updated.transaction_time is not None
        assert updated.updated_at > created.created_at
    
    @pytest.mark.unit
    def test_list_payments(self, payment_store, db_session):
        """Test listing payments."""
        # Create multiple payments
        for i in range(5):
            payment_store.create_payment(
                db_session,
                order_id=f"ORD-{i}",
                amount=Decimal("100.00"),
                bill_code=f"ABC{i}",
            )
        db_session.commit()
        
        # List all payments
        payments = payment_store.list_payments(db_session)
        assert len(payments) == 5
        
        # List with limit
        payments = payment_store.list_payments(db_session, limit=3)
        assert len(payments) == 3
        
        # List with offset
        payments = payment_store.list_payments(db_session, limit=2, offset=2)
        assert len(payments) == 2
    
    @pytest.mark.unit
    def test_list_payments_by_status(self, payment_store, db_session):
        """Test listing payments filtered by status."""
        # Create payments with different statuses
        payment1 = payment_store.create_payment(
            db_session,
            order_id="ORD-1",
            amount=Decimal("100.00"),
            bill_code="ABC1",
        )
        
        payment2 = payment_store.create_payment(
            db_session,
            order_id="ORD-2",
            amount=Decimal("200.00"),
            bill_code="ABC2",
        )
        db_session.commit()
        
        # Update one to success
        payment_store.update_payment_status(
            db_session,
            payment1.id,
            PaymentStatus.SUCCESS
        )
        db_session.commit()
        
        # List only successful payments
        payments = payment_store.list_payments(
            db_session,
            status=PaymentStatus.SUCCESS
        )
        assert len(payments) == 1
        assert payments[0].order_id == "ORD-1"
        
        # List only pending payments
        payments = payment_store.list_payments(
            db_session,
            status=PaymentStatus.PENDING
        )
        assert len(payments) == 1
        assert payments[0].order_id == "ORD-2"
    
    @pytest.mark.unit
    def test_soft_delete_payment(self, payment_store, db_session):
        """Test soft deleting a payment."""
        # Create payment
        created = payment_store.create_payment(
            db_session,
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.commit()
        
        # Soft delete
        deleted = payment_store.soft_delete_payment(db_session, created.id)
        db_session.commit()
        
        assert deleted is not None
        assert deleted.deleted_at is not None
        
        # Should not be found in normal queries
        payment = payment_store.get_payment(db_session, created.id)
        assert payment is None
        
        # But still exists in database
        unscoped_payment = db_session.query(PaymentModel).filter(
            PaymentModel.id == created.id
        ).first()
        assert unscoped_payment is not None
        assert unscoped_payment.deleted_at is not None
    
    @pytest.mark.unit
    def test_list_payments_excludes_deleted(self, payment_store, db_session):
        """Test listing payments excludes soft deleted records."""
        # Create payments
        payment1 = payment_store.create_payment(
            db_session,
            order_id="ORD-1",
            amount=Decimal("100.00"),
            bill_code="ABC1",
        )
        
        payment2 = payment_store.create_payment(
            db_session,
            order_id="ORD-2",
            amount=Decimal("200.00"),
            bill_code="ABC2",
        )
        db_session.commit()
        
        # Soft delete one
        payment_store.soft_delete_payment(db_session, payment1.id)
        db_session.commit()
        
        # List should only include non-deleted
        payments = payment_store.list_payments(db_session)
        assert len(payments) == 1
        assert payments[0].order_id == "ORD-2"
    
    @pytest.mark.unit
    def test_payment_model_defaults(self, db_session):
        """Test payment model default values."""
        payment = PaymentModel(
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            bill_code="ABC123",
        )
        db_session.add(payment)
        db_session.commit()
        
        assert payment.id is not None  # Auto-generated
        assert payment.currency == "MYR"
        assert payment.status == PaymentStatus.PENDING
        assert payment.tp_bill_charge_to_customer is True
        assert payment.created_at is not None
        assert payment.deleted_at is None