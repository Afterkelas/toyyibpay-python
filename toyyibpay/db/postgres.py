"""PostgreSQL database integration for ToyyibPay SDK."""

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Numeric,
    Integer,
    DateTime,
    Boolean,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from ..enums import PaymentStatus
from ..utils import generate_ulid

Base = declarative_base()


class PaymentModel(Base):
    """SQLAlchemy model for payments."""
    
    __tablename__ = "payments"
    
    id = Column(String(50), primary_key=True, default=generate_ulid)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    bill_code = Column(String(12), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="MYR")
    status = Column(Integer, default=PaymentStatus.PENDING)
    
    # Customer information
    customer_name = Column(String(255))
    customer_email = Column(String(255))
    customer_phone = Column(String(20))
    
    # ToyyibPay specific fields
    tp_channel = Column(Integer)
    tp_category_code = Column(String(12))
    tp_bill_description = Column(String(255))
    tp_transaction_message = Column(String(255))
    tp_transaction_ref = Column(String(100))
    tp_return_url = Column(String(255))
    tp_callback_url = Column(String(255))
    tp_bill_charge_to_customer = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime)
    transaction_time = Column(DateTime)


class PostgresPaymentStore:
    """PostgreSQL payment store for ToyyibPay SDK.
    
    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine("postgresql://user:pass@localhost/mydb")
        >>> store = PostgresPaymentStore(engine)
        >>> store.create_tables()
    """
    
    def __init__(self, engine: Engine):
        """Initialize PostgreSQL payment store.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def create_tables(self) -> None:
        """Create database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_payment(
        self,
        session: Session,
        order_id: str,
        amount: Decimal,
        bill_code: str,
        customer_name: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        **kwargs: Any
    ) -> PaymentModel:
        """Create a new payment record.
        
        Args:
            session: Database session
            order_id: Order ID
            amount: Payment amount
            bill_code: ToyyibPay bill code
            customer_name: Customer name
            customer_email: Customer email
            customer_phone: Customer phone
            **kwargs: Additional fields
        
        Returns:
            Created payment model
        """
        payment = PaymentModel(
            order_id=order_id,
            amount=amount,
            bill_code=bill_code,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            **kwargs
        )
        session.add(payment)
        session.flush()
        return payment
    
    def get_payment(self, session: Session, payment_id: str) -> Optional[PaymentModel]:
        """Get payment by ID.
        
        Args:
            session: Database session
            payment_id: Payment ID
        
        Returns:
            Payment model or None
        """
        return session.query(PaymentModel).filter(
            PaymentModel.id == payment_id,
            PaymentModel.deleted_at.is_(None)
        ).first()
    
    def get_payment_by_order_id(
        self, 
        session: Session, 
        order_id: str
    ) -> Optional[PaymentModel]:
        """Get payment by order ID.
        
        Args:
            session: Database session
            order_id: Order ID
        
        Returns:
            Payment model or None
        """
        return session.query(PaymentModel).filter(
            PaymentModel.order_id == order_id,
            PaymentModel.deleted_at.is_(None)
        ).first()
    
    def get_payment_by_bill_code(
        self, 
        session: Session, 
        bill_code: str
    ) -> Optional[PaymentModel]:
        """Get payment by bill code.
        
        Args:
            session: Database session
            bill_code: ToyyibPay bill code
        
        Returns:
            Payment model or None
        """
        return session.query(PaymentModel).filter(
            PaymentModel.bill_code == bill_code,
            PaymentModel.deleted_at.is_(None)
        ).first()
    
    def update_payment_status(
        self,
        session: Session,
        payment_id: str,
        status: PaymentStatus,
        transaction_ref: Optional[str] = None,
        transaction_message: Optional[str] = None,
        transaction_time: Optional[str] = None,
    ) -> Optional[PaymentModel]:
        """Update payment status.
        
        Args:
            session: Database session
            payment_id: Payment ID
            status: New payment status
            transaction_ref: Transaction reference
            transaction_message: Transaction message
            transaction_time: Transaction time
        
        Returns:
            Updated payment model or None
        """
        payment = self.get_payment(session, payment_id)
        if payment:
            payment.status = status
            payment.updated_at = datetime.utcnow()
            
            if transaction_ref:
                payment.tp_transaction_ref = transaction_ref
            if transaction_message:
                payment.tp_transaction_message = transaction_message
            if transaction_time:
                payment.transaction_time = datetime.fromisoformat(
                    transaction_time.replace("Z", "+00:00")
                )
            
            session.flush()
        return payment
    
    def list_payments(
        self,
        session: Session,
        status: Optional[PaymentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[PaymentModel]:
        """List payments with optional filtering.
        
        Args:
            session: Database session
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of payment models
        """
        query = session.query(PaymentModel).filter(
            PaymentModel.deleted_at.is_(None)
        )
        
        if status is not None:
            query = query.filter(PaymentModel.status == status)
        
        return query.order_by(
            PaymentModel.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    def soft_delete_payment(
        self,
        session: Session,
        payment_id: str
    ) -> Optional[PaymentModel]:
        """Soft delete a payment.
        
        Args:
            session: Database session
            payment_id: Payment ID
        
        Returns:
            Deleted payment model or None
        """
        payment = self.get_payment(session, payment_id)
        if payment:
            payment.deleted_at = datetime.utcnow()
            session.flush()
        return payment