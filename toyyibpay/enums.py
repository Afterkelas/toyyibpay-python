"""Enumerations for ToyyibPay SDK."""

from enum import IntEnum


class PaymentStatus(IntEnum):
    """Payment status enumerations."""
    
    SUCCESS = 1
    PENDING = 2
    FAILED = 3
    PENDING_TRANSACTION = 4


class PaymentChannel(IntEnum):
    """Payment channel enumerations."""
    
    FPX = 0
    CREDIT_CARD = 1
    FPX_AND_CREDIT_CARD = 2


class ChargeParty(IntEnum):
    """Charge party enumerations."""
    
    CUSTOMER = 0
    OWNER = 1


class PriceVariable(IntEnum):
    """Price variable settings."""
    
    VARIABLE = 0
    FIXED = 1


class PayerInfo(IntEnum):
    """Payer info visibility settings."""
    
    HIDE = 0
    SHOW = 1


class Environment(str):
    """Environment settings."""
    
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


# Default values
DEFAULT_BILL_EXPIRY = 1  # 1-100 days
CORPORATE_BANKING_THRESHOLD = 30000  # Amount in smallest currency unit