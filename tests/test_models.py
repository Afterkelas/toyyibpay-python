"""Tests for ToyyibPay models."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from toyyibpay.models import (
    CreateBillInput,
    BillResponse,
    CallbackData,
    TransactionData,
    PaymentRecord,
    APIResponse,
    InitPaymentInput,
    CategoryInput,
)
from toyyibpay.enums import PaymentStatus, PaymentChannel, ChargeParty, PriceVariable, PayerInfo


class TestCreateBillInput:
    """Test CreateBillInput model."""
    
    @pytest.mark.unit
    def test_create_bill_input_valid(self):
        """Test creating valid bill input."""
        bill_input = CreateBillInput(
            category_code="CAT123",
            bill_name="BILL123",
            bill_description="Test payment",
            bill_amount=100.00,
            bill_return_url="https://example.com/return",
            bill_callback_url="https://example.com/callback",
            bill_external_reference_no="ORD-12345",
            bill_to="John Doe",
            bill_email="john@example.com",
            bill_phone="0123456789",
        )
        
        assert bill_input.category_code == "CAT123"
        assert bill_input.bill_amount == 10000  # Converted to cents
        assert bill_input.bill_price_setting == PriceVariable.FIXED
        assert bill_input.bill_payor_info == PayerInfo.SHOW
        assert bill_input.bill_payment_channel == PaymentChannel.FPX_AND_CREDIT_CARD
    
    @pytest.mark.unit
    def test_create_bill_input_amount_conversion(self):
        """Test amount is converted to cents."""
        bill_input = CreateBillInput(
            category_code="CAT123",
            bill_name="BILL123",
            bill_description="Test",
            bill_amount=99.99,
            bill_return_url="https://example.com",
            bill_callback_url="https://example.com",
            bill_external_reference_no="ORD-12345",
            bill_to="John Doe",
            bill_email="john@example.com",
            bill_phone="0123456789",
        )
        
        assert bill_input.bill_amount == 9999
    
    @pytest.mark.unit
    def test_create_bill_input_invalid_email(self):
        """Test invalid email validation."""
        with pytest.raises(PydanticValidationError) as exc_info:
            CreateBillInput(
                category_code="CAT123",
                bill_name="BILL123",
                bill_description="Test",
                bill_amount=100.00,
                bill_return_url="https://example.com",
                bill_callback_url="https://example.com",
                bill_external_reference_no="ORD-12345",
                bill_to="John Doe",
                bill_email="invalid-email",
                bill_phone="0123456789",
            )
        
        assert "valid email address" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_bill_input_invalid_amount(self):
        """Test invalid amount validation."""
        with pytest.raises(PydanticValidationError) as exc_info:
            CreateBillInput(
                category_code="CAT123",
                bill_name="BILL123",
                bill_description="Test",
                bill_amount=-10.00,
                bill_return_url="https://example.com",
                bill_callback_url="https://example.com",
                bill_external_reference_no="ORD-12345",
                bill_to="John Doe",
                bill_email="john@example.com",
                bill_phone="0123456789",
            )
        
        assert "greater than 0" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_bill_input_alphanumeric_validation(self):
        """Test alphanumeric validation for bill name and description."""
        with pytest.raises(PydanticValidationError) as exc_info:
            CreateBillInput(
                category_code="CAT123",
                bill_name="Bill@123!",  # Invalid characters
                bill_description="Test payment",
                bill_amount=100.00,
                bill_return_url="https://example.com",
                bill_callback_url="https://example.com",
                bill_external_reference_no="ORD-12345",
                bill_to="John Doe",
                bill_email="john@example.com",
                bill_phone="0123456789",
            )
        
        assert "alphanumeric characters" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_create_bill_input_field_aliases(self):
        """Test field aliases work correctly."""
        data = {
            "categoryCode": "CAT123",
            "billName": "BILL123",
            "billDescription": "Test",
            "billAmount": 100.00,
            "billReturnUrl": "https://example.com",
            "billCallbackUrl": "https://example.com",
            "billExternalReferenceNo": "ORD-12345",
            "billTo": "John Doe",
            "billEmail": "john@example.com",
            "billPhone": "0123456789",
        }
        
        bill_input = CreateBillInput(**data)
        assert bill_input.category_code == "CAT123"
    
    @pytest.mark.unit
    def test_create_bill_input_serialization(self):
        """Test model serialization with aliases."""
        bill_input = CreateBillInput(
            category_code="CAT123",
            bill_name="BILL123",
            bill_description="Test",
            bill_amount=100.00,
            bill_return_url="https://example.com",
            bill_callback_url="https://example.com",
            bill_external_reference_no="ORD-12345",
            bill_to="John Doe",
            bill_email="john@example.com",
            bill_phone="0123456789",
        )
        
        serialized = bill_input.model_dump(by_alias=True)
        assert serialized["categoryCode"] == "CAT123"
        assert serialized["billAmount"] == 10000


class TestBillResponse:
    """Test BillResponse model."""
    
    @pytest.mark.unit
    def test_bill_response_creation(self):
        """Test creating bill response."""
        response = BillResponse(bill_code="ABC123")
        assert response.bill_code == "ABC123"
        assert "ABC123" in response.payment_url
    
    @pytest.mark.unit
    def test_bill_response_with_alias(self):
        """Test bill response with field alias."""
        response = BillResponse(BillCode="ABC123")
        assert response.bill_code == "ABC123"


class TestCallbackData:
    """Test CallbackData model."""
    
    @pytest.mark.unit
    def test_callback_data_valid(self):
        """Test valid callback data."""
        callback = CallbackData(
            ref_no="REF123",
            order_id="ORD-12345",
            bill_code="ABC123",
            status=PaymentStatus.SUCCESS,
            amount=10000,  # In cents
            transaction_time="2025-01-15 10:30:00",
        )
        
        assert callback.ref_no == "REF123"
        assert callback.order_id == "ORD-12345"
        assert callback.status == PaymentStatus.SUCCESS
        assert callback.amount == 100.00  # Converted from cents
    
    @pytest.mark.unit
    def test_callback_data_amount_conversion(self):
        """Test amount is converted from cents."""
        callback = CallbackData(
            ref_no="REF123",
            order_id="ORD-12345",
            bill_code="ABC123",
            status=1,
            amount=9999,
            transaction_time="2025-01-15 10:30:00",
        )
        
        assert callback.amount == 99.99
    
    @pytest.mark.unit
    def test_callback_data_with_reason(self):
        """Test callback data with failure reason."""
        callback = CallbackData(
            ref_no="REF123",
            order_id="ORD-12345",
            bill_code="ABC123",
            status=PaymentStatus.FAILED,
            reason="Insufficient funds",
            amount=10000,
            transaction_time="2025-01-15 10:30:00",
        )
        
        assert callback.reason == "Insufficient funds"


class TestTransactionData:
    """Test TransactionData model."""
    
    @pytest.mark.unit
    def test_transaction_data_valid(self):
        """Test valid transaction data."""
        transaction = TransactionData(
            bill_name="BILL123",
            bill_description="Test payment",
            bill_to="John Doe",
            bill_email="john@example.com",
            bill_phone="0123456789",
            bill_status=PaymentStatus.SUCCESS,
            bill_payment_status=PaymentStatus.SUCCESS,
            bill_payment_amount=100.00,
            bill_payment_date=datetime(2025, 1, 15, 10, 30, 0),
            bill_payment_channel="FPX",
            bill_payment_invoice_no="INV123",
            bill_external_reference_no="ORD-12345",
            bill_split_payment=False,
        )
        
        assert transaction.bill_name == "BILL123"
        assert transaction.bill_payment_status == PaymentStatus.SUCCESS
        assert transaction.bill_payment_amount == 100.00
        assert not transaction.bill_split_payment


class TestPaymentRecord:
    """Test PaymentRecord model."""
    
    @pytest.mark.unit
    def test_payment_record_valid(self):
        """Test valid payment record."""
        now = datetime.now()
        payment = PaymentRecord(
            id="ULID123",
            order_id="ORD-12345",
            amount=Decimal("100.00"),
            currency="MYR",
            status=PaymentStatus.PENDING,
            tp_channel=PaymentChannel.FPX,
            tp_bill_code="ABC123",
            tp_category_code="CAT123",
            tp_bill_description="Test payment",
            tp_return_url="https://example.com/return",
            tp_callback_url="https://example.com/callback",
            created_at=now,
            updated_at=now,
        )
        
        assert payment.id == "ULID123"
        assert payment.amount == Decimal("100.00")
        assert payment.status == PaymentStatus.PENDING
        assert payment.currency == "MYR"


class TestInitPaymentInput:
    """Test InitPaymentInput model."""
    
    @pytest.mark.unit
    def test_init_payment_input_valid(self):
        """Test valid payment initialization input."""
        payment_input = InitPaymentInput(
            order_id="ORD-12345",
            name="John Doe",
            email="john@example.com",
            phone="0123456789",
            amount=Decimal("100.00"),
        )
        
        assert payment_input.order_id == "ORD-12345"
        assert payment_input.amount == Decimal("100.00")
    
    @pytest.mark.unit
    def test_init_payment_input_decimal_validation(self):
        """Test decimal validation for amount."""
        with pytest.raises(PydanticValidationError) as exc_info:
            InitPaymentInput(
                order_id="ORD-12345",
                name="John Doe",
                email="john@example.com",
                phone="0123456789",
                amount=Decimal("100.999"),  # Too many decimal places
            )
        
        assert "more than 2 decimal places" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_init_payment_input_with_return_url(self):
        """Test payment input with optional return URL."""
        payment_input = InitPaymentInput(
            order_id="ORD-12345",
            name="John Doe",
            email="john@example.com",
            phone="0123456789",
            amount=Decimal("100.00"),
            return_url="https://example.com/custom-return",
        )
        
        assert payment_input.return_url == "https://example.com/custom-return"


class TestAPIResponse:
    """Test APIResponse model."""
    
    @pytest.mark.unit
    def test_api_response_success(self):
        """Test successful API response."""
        response = APIResponse(
            message="Payment created successfully",
            success=True,
            status_code=200,
            status_text="OK",
            payload={"bill_code": "ABC123"},
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.payload["bill_code"] == "ABC123"
    
    @pytest.mark.unit
    def test_api_response_failure(self):
        """Test failed API response."""
        response = APIResponse(
            message="Invalid request",
            success=False,
            status_code=400,
            status_text="Bad Request",
        )
        
        assert response.success is False
        assert response.status_code == 400
        assert response.payload is None


class TestCategoryInput:
    """Test CategoryInput model."""
    
    @pytest.mark.unit
    def test_category_input_valid(self):
        """Test valid category input."""
        category = CategoryInput(
            name="Test Category",
            description="This is a test category",
        )
        
        assert category.name == "Test Category"
        assert category.description == "This is a test category"
    
    @pytest.mark.unit
    def test_category_input_max_length(self):
        """Test category input field length validation."""
        with pytest.raises(PydanticValidationError):
            CategoryInput(
                name="A" * 51,  # Exceeds max length
                description="Valid description",
            )