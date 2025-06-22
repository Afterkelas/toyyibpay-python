"""Pydantic models for ToyyibPay SDK."""

from datetime import datetime
from typing import Optional, Any, Dict
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict, field_serializer

from .enums import (
    PaymentStatus,
    PaymentChannel,
    ChargeParty,
    PriceVariable,
    PayerInfo,
)


class ToyyibPayModel(BaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S"),
            Decimal: lambda v: float(v),
        }
    )


class CreateBillInput(ToyyibPayModel):
    """Input model for creating a bill."""

    category_code: str = Field(
        ...,
        alias="categoryCode",
        max_length=12
    )
    bill_name: str = Field(
        ...,
        alias="billName",
        max_length=30
    )
    bill_description: str = Field(
        ...,
        alias="billDescription",
        max_length=100
    )
    bill_price_setting: PriceVariable = Field(
        PriceVariable.FIXED,
        alias="billPriceSetting"
    )
    bill_payor_info: PayerInfo = Field(
        PayerInfo.SHOW,
        alias="billPayorInfo"
    )
    bill_amount: float = Field(
        ...,
        alias="billAmount",
        gt=0
    )
    bill_return_url: str = Field(
        ...,
        alias="billReturnUrl",
        max_length=255
    )
    bill_callback_url: str = Field(
        ...,
        alias="billCallbackUrl",
        max_length=255
    )
    bill_external_reference_no: str = Field(
        ...,
        alias="billExternalReferenceNo",
        max_length=50
    )
    bill_to: str = Field(..., alias="billTo", max_length=255)
    bill_email: EmailStr = Field(..., alias="billEmail")
    bill_phone: str = Field(..., alias="billPhone", max_length=20)
    bill_content_email: Optional[str] = Field(
        None,
        alias="billContentEmail",
        max_length=1000
    )
    bill_expiry_date: Optional[str] = Field(None, alias="billExpiryDate")
    bill_expiry_days: Optional[int] = Field(
        1,
        alias="billExpiryDays",
        ge=1,
        le=100
    )
    bill_split_payment: Optional[int] = Field(0, alias="billSplitPayment")
    bill_split_payment_args: Optional[str] = Field(
        None,
        alias="billSplitPaymentArgs"
    )
    bill_payment_channel: PaymentChannel = Field(
        PaymentChannel.FPX_AND_CREDIT_CARD,
        alias="billPaymentChannel"
    )
    bill_charge_to_customer: ChargeParty = Field(
        ChargeParty.CUSTOMER,
        alias="billChargeToCustomer"
    )
    charge_fpx_b2b: ChargeParty = Field(
        ChargeParty.CUSTOMER,
        alias="chargeFPXB2B"
    )
    enable_fpx_b2b: int = Field(0, alias="enableFPXB2B")

    @field_validator("bill_amount")
    @classmethod
    def convert_to_cents(cls, v: float) -> float:
        """Convert amount to cents (smallest currency unit)."""
        return v * 100

    @field_validator("bill_name", "bill_description")
    @classmethod
    def validate_alphanumeric(cls, v: str) -> str:
        """Validate alphanumeric characters, space and underscore only."""
        import re
        if not re.match(r'^[a-zA-Z0-9 _]+$', v):
            raise ValueError(
                "Only alphanumeric characters, space and underscore allowed"
            )
        return v

    @field_serializer("bill_price_setting")
    def serialize_price_setting(self, value: PriceVariable) -> int:
        """Serialize PriceVariable enum to int."""
        return int(value)

    @field_serializer("bill_payor_info")
    def serialize_payor_info(self, value: PayerInfo) -> int:
        """Serialize PayerInfo enum to int."""
        return int(value)

    @field_serializer("bill_payment_channel")
    def serialize_payment_channel(self, value: PaymentChannel) -> int:
        """Serialize PaymentChannel enum to int."""
        return int(value)

    @field_serializer("bill_charge_to_customer")
    def serialize_charge_to_customer(self, value: ChargeParty) -> int:
        """Serialize ChargeParty enum to int."""
        return int(value)

    @field_serializer("charge_fpx_b2b")
    def serialize_charge_fpx_b2b(self, value: ChargeParty) -> int:
        """Serialize ChargeParty enum to int."""
        return int(value)


class BillResponse(ToyyibPayModel):
    """Response model for bill creation."""

    bill_code: str = Field(..., alias="BillCode")

    @property
    def payment_url(self) -> str:
        """Generate payment URL from bill code."""
        # This will be dynamically set based on environment
        return f"https://toyyibpay.com/{self.bill_code}"


class CallbackData(ToyyibPayModel):
    """Webhook callback data from ToyyibPay."""

    ref_no: str = Field(..., alias="refno")
    order_id: str = Field(..., alias="order_id")
    bill_code: str = Field(..., alias="billcode")
    status: PaymentStatus = Field(..., alias="status")
    reason: Optional[str] = Field(None, alias="reason")
    amount: float = Field(..., alias="amount")
    transaction_time: str = Field(..., alias="transaction_time")

    @field_validator("amount")
    @classmethod
    def convert_from_cents(cls, v: float) -> float:
        """Convert amount from cents to standard currency unit."""
        return v / 100


class TransactionData(ToyyibPayModel):
    """Transaction data model."""

    bill_name: str = Field(..., alias="billName")
    bill_description: str = Field(..., alias="billDescription")
    bill_to: str = Field(..., alias="billTo")
    bill_email: str = Field(..., alias="billEmail")
    bill_phone: str = Field(..., alias="billPhone")
    bill_status: PaymentStatus = Field(..., alias="billStatus")
    bill_payment_status: PaymentStatus = Field(..., alias="billpaymentStatus")
    bill_payment_amount: float = Field(..., alias="billpaymentAmount")
    bill_payment_date: datetime = Field(..., alias="billPaymentDate")
    bill_payment_channel: str = Field(..., alias="billpaymentChannel")
    bill_payment_invoice_no: str = Field(..., alias="billpaymentInvoiceNo")
    bill_external_reference_no: str = Field(
        ...,
        alias="billExternalReferenceNo"
    )
    bill_payment_settlement: Optional[str] = Field(
        None,
        alias="billpaymentSettlement"
    )
    settlement_reference_no: Optional[str] = Field(
        None,
        alias="settlementReferenceNo"
    )
    bill_split_payment: bool = Field(..., alias="billSplitPayment")
    bill_split_payment_args: Optional[str] = Field(
        None,
        alias="billSplitPaymentArgs"
    )


class PaymentRecord(ToyyibPayModel):
    """Internal payment record model."""

    id: str
    order_id: str
    amount: Decimal
    currency: str = "MYR"
    status: PaymentStatus = PaymentStatus.PENDING

    # ToyyibPay specific fields
    tp_channel: PaymentChannel
    tp_bill_code: str
    tp_category_code: str
    tp_bill_description: str
    tp_transaction_message: Optional[str] = None
    tp_return_url: str
    tp_callback_url: str
    tp_bill_charge_to_customer: bool = True

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class APIResponse(ToyyibPayModel):
    """Standard API response format."""

    message: str = ""
    success: bool = True
    status_code: int = Field(200, alias="statusCode")
    status_text: str = Field("OK", alias="statusText")
    payload: Optional[Any] = None


class InitPaymentInput(ToyyibPayModel):
    """Input for initiating a payment."""

    order_id: str = Field(..., alias="orderId", max_length=50)
    name: str = Field(..., max_length=255)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    amount: Decimal = Field(..., gt=0)
    return_url: Optional[str] = Field(None, alias="returnURL", max_length=255)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class CategoryInput(ToyyibPayModel):
    """Input for creating a category."""

    name: str = Field(..., max_length=50)
    description: str = Field(..., max_length=100)
