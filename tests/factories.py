"""Test data factories for ToyyibPay SDK tests."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

import factory
from factory import fuzzy
from faker import Faker

from toyyibpay.models import (
    CreateBillInput,
    BillResponse,
    CallbackData,
    TransactionData,
    PaymentRecord,
    InitPaymentInput,
    CategoryInput,
)
from toyyibpay.enums import PaymentStatus, PaymentChannel
from toyyibpay.utils import generate_ulid, generate_order_id

fake = Faker()


class CreateBillInputFactory(factory.Factory):
    """Factory for CreateBillInput test data."""
    
    class Meta:
        model = CreateBillInput
    
    category_code = factory.LazyAttribute(lambda _: f"CAT{fake.random_number(digits=5)}")
    bill_name = factory.LazyAttribute(lambda _: f"BILL_{fake.uuid4()[:8].upper()}")
    bill_description = factory.LazyAttribute(lambda _: fake.sentence(nb_words=5))
    bill_amount = factory.LazyAttribute(lambda _: float(fake.random_number(digits=3)))
    bill_return_url = factory.LazyAttribute(lambda _: fake.url())
    bill_callback_url = factory.LazyAttribute(lambda _: fake.url())
    bill_external_reference_no = factory.LazyAttribute(lambda _: generate_order_id())
    bill_to = factory.LazyAttribute(lambda _: fake.name())
    bill_email = factory.LazyAttribute(lambda _: fake.email())
    bill_phone = factory.LazyAttribute(lambda _: f"01{fake.random_number(digits=8)}")
    
    @factory.lazy_attribute
    def bill_expiry_days(self):
        return fake.random_int(min=1, max=30)


class BillResponseFactory(factory.Factory):
    """Factory for BillResponse test data."""
    
    class Meta:
        model = dict  # Return dict since BillResponse is simple
    
    bill_code = factory.LazyAttribute(lambda _: fake.lexify("????????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))


class CallbackDataFactory(factory.Factory):
    """Factory for CallbackData test data."""
    
    class Meta:
        model = dict  # Return dict for easy modification
    
    ref_no = factory.LazyAttribute(lambda _: f"REF{fake.random_number(digits=8)}")
    order_id = factory.LazyAttribute(lambda _: generate_order_id())
    bill_code = factory.LazyAttribute(lambda _: fake.lexify("????????"))
    status = fuzzy.FuzzyChoice([1, 2, 3, 4])  # Payment statuses
    reason = factory.LazyAttribute(lambda obj: "" if obj.status == 1 else fake.sentence())
    amount = factory.LazyAttribute(lambda _: fake.random_number(digits=5))  # In cents
    transaction_time = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-1hour").strftime("%Y-%m-%d %H:%M:%S")
    )


class TransactionDataFactory(factory.Factory):
    """Factory for TransactionData test data."""
    
    class Meta:
        model = dict  # Return dict for flexibility
    
    bill_name = factory.LazyAttribute(lambda _: f"BILL_{fake.uuid4()[:8].upper()}")
    bill_description = factory.LazyAttribute(lambda _: fake.sentence())
    bill_to = factory.LazyAttribute(lambda _: fake.name())
    bill_email = factory.LazyAttribute(lambda _: fake.email())
    bill_phone = factory.LazyAttribute(lambda _: f"01{fake.random_number(digits=8)}")
    bill_status = factory.LazyAttribute(lambda _: str(fake.random_int(1, 4)))
    bill_payment_status = factory.LazyAttribute(lambda _: str(fake.random_int(1, 4)))
    bill_payment_amount = factory.LazyAttribute(lambda _: f"{fake.random_number(digits=3)}.00")
    bill_payment_date = factory.LazyAttribute(
        lambda _: fake.date_time_between(start_date="-30days").strftime("%d-%m-%Y %H:%M:%S")
    )
    bill_payment_channel = fuzzy.FuzzyChoice(["FPX", "Credit Card", "FPX B2B"])
    bill_payment_invoice_no = factory.LazyAttribute(lambda _: f"INV{fake.random_number(digits=6)}")
    bill_external_reference_no = factory.LazyAttribute(lambda _: generate_order_id())
    bill_split_payment = "0"


class PaymentRecordFactory(factory.Factory):
    """Factory for PaymentRecord test data."""
    
    class Meta:
        model = dict  # Return dict for database model
    
    id = factory.LazyAttribute(lambda _: generate_ulid())
    order_id = factory.LazyAttribute(lambda _: generate_order_id())
    amount = factory.LazyAttribute(lambda _: Decimal(str(fake.random_number(digits=3))))
    currency = "MYR"
    status = fuzzy.FuzzyChoice(list(PaymentStatus))
    
    # Customer info
    customer_name = factory.LazyAttribute(lambda _: fake.name())
    customer_email = factory.LazyAttribute(lambda _: fake.email())
    customer_phone = factory.LazyAttribute(lambda _: f"01{fake.random_number(digits=8)}")
    
    # ToyyibPay fields
    tp_channel = fuzzy.FuzzyChoice(list(PaymentChannel))
    tp_bill_code = factory.LazyAttribute(lambda _: fake.lexify("????????"))
    tp_category_code = factory.LazyAttribute(lambda _: f"CAT{fake.random_number(digits=5)}")
    tp_bill_description = factory.LazyAttribute(lambda _: fake.sentence())
    tp_return_url = factory.LazyAttribute(lambda _: fake.url())
    tp_callback_url = factory.LazyAttribute(lambda _: fake.url())
    tp_bill_charge_to_customer = True
    
    # Timestamps
    created_at = factory.LazyAttribute(lambda _: datetime.now())
    updated_at = factory.LazyAttribute(lambda _: datetime.now())


class InitPaymentInputFactory(factory.Factory):
    """Factory for InitPaymentInput test data."""
    
    class Meta:
        model = InitPaymentInput
    
    order_id = factory.LazyAttribute(lambda _: generate_order_id())
    name = factory.LazyAttribute(lambda _: fake.name())
    email = factory.LazyAttribute(lambda _: fake.email())
    phone = factory.LazyAttribute(lambda _: f"01{fake.random_number(digits=8)}")
    amount = factory.LazyAttribute(lambda _: Decimal(str(fake.random_number(digits=3))))
    return_url = factory.LazyAttribute(lambda _: fake.url() if fake.boolean() else None)


class CategoryInputFactory(factory.Factory):
    """Factory for CategoryInput test data."""
    
    class Meta:
        model = CategoryInput
    
    name = factory.LazyAttribute(lambda _: fake.company())
    description = factory.LazyAttribute(lambda _: fake.catch_phrase())


class BatchDataFactory:
    """Factory for creating batches of test data."""
    
    @staticmethod
    def create_payment_batch(count: int = 10, **kwargs) -> list[Dict[str, Any]]:
        """Create a batch of payment records."""
        payments = []
        for i in range(count):
            payment_data = PaymentRecordFactory.create(**kwargs)
            # Ensure unique order IDs
            payment_data["order_id"] = f"ORD-BATCH-{i:04d}"
            payments.append(payment_data)
        return payments
    
    @staticmethod
    def create_transaction_history(
        bill_code: str,
        count: int = 5,
        status: Optional[PaymentStatus] = None
    ) -> list[Dict[str, Any]]:
        """Create transaction history for a bill."""
        transactions = []
        base_date = datetime.now()
        
        for i in range(count):
            tx_data = TransactionDataFactory.create()
            tx_data["billcode"] = bill_code
            
            # Set sequential dates
            tx_date = base_date - timedelta(days=count-i)
            tx_data["billPaymentDate"] = tx_date.strftime("%d-%m-%Y %H:%M:%S")
            
            # Set status if specified
            if status:
                tx_data["billpaymentStatus"] = str(int(status))
            
            transactions.append(tx_data)
        
        return transactions
    
    @staticmethod
    def create_webhook_sequence(order_id: str) -> list[Dict[str, Any]]:
        """Create a sequence of webhook callbacks for testing state transitions."""
        bill_code = fake.lexify("????????")
        ref_no = f"REF{fake.random_number(digits=8)}"
        
        # Pending -> Success sequence
        return [
            {
                "refno": ref_no,
                "order_id": order_id,
                "billcode": bill_code,
                "status": 2,  # Pending
                "reason": "",
                "amount": 10000,
                "transaction_time": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "refno": ref_no,
                "order_id": order_id,
                "billcode": bill_code,
                "status": 1,  # Success
                "reason": "",
                "amount": 10000,
                "transaction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ]


class MockDataGenerator:
    """Generate mock data for specific test scenarios."""
    
    @staticmethod
    def create_fpx_transaction() -> Dict[str, Any]:
        """Create FPX-specific transaction data."""
        data = TransactionDataFactory.create()
        data["billpaymentChannel"] = "FPX"
        data["billpaymentStatus"] = "1"  # Success
        return data
    
    @staticmethod
    def create_credit_card_transaction() -> Dict[str, Any]:
        """Create credit card-specific transaction data."""
        data = TransactionDataFactory.create()
        data["billpaymentChannel"] = "Credit Card"
        data["billpaymentStatus"] = "1"  # Success
        return data
    
    @staticmethod
    def create_failed_payment() -> Dict[str, Any]:
        """Create failed payment data."""
        data = CallbackDataFactory.create()
        data["status"] = 3  # Failed
        data["reason"] = fake.random_element([
            "Insufficient funds",
            "Transaction timeout",
            "Card declined",
            "Invalid account",
            "User cancelled",
        ])
        return data
    
    @staticmethod
    def create_corporate_payment() -> Dict[str, Any]:
        """Create corporate banking payment data."""
        payment = InitPaymentInputFactory.create()
        # Set amount above corporate threshold
        payment.amount = Decimal("35000.00")
        return payment.model_dump()


# Convenience functions
def create_test_bill(**kwargs) -> Dict[str, Any]:
    """Create test bill data with defaults."""
    defaults = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "0123456789",
        "amount": 100.00,
        "order_id": generate_order_id("TEST"),
    }
    defaults.update(kwargs)
    return defaults


def create_test_webhook(**kwargs) -> Dict[str, Any]:
    """Create test webhook data with defaults."""
    defaults = CallbackDataFactory.create()
    defaults.update(kwargs)
    return defaults


def create_test_config(**kwargs) -> Dict[str, Any]:
    """Create test configuration with defaults."""
    defaults = {
        "api_key": f"test-key-{fake.uuid4()[:8]}",
        "category_id": f"CAT{fake.random_number(digits=5)}",
        "environment": "dev",
        "return_url": "https://test.example.com/return",
        "callback_url": "https://test.example.com/callback",
    }
    defaults.update(kwargs)
    return defaults