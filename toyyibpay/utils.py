"""Utility functions for ToyyibPay SDK."""

import time
import random
import string
from datetime import datetime
from typing import Any, Dict, Optional, Union
from decimal import Decimal, ROUND_HALF_UP


def generate_ulid() -> str:
    """Generate a ULID (Universally Unique Lexicographically Sortable Identifier).
    
    Similar to the Go SDK's uid.ULID() function.
    
    Returns:
        A 26-character ULID string
    """
    # Timestamp (48 bits)
    timestamp = int(time.time() * 1000)
    
    # Randomness (80 bits)
    randomness = random.getrandbits(80)
    
    # Combine timestamp and randomness
    ulid_int = (timestamp << 80) | randomness
    
    # Convert to base32
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    ulid = ""
    
    for _ in range(26):
        ulid = alphabet[ulid_int & 0x1F] + ulid
        ulid_int >>= 5
    
    return ulid


def generate_order_id(prefix: str = "ORD") -> str:
    """Generate a unique order ID.
    
    Args:
        prefix: Prefix for the order ID
    
    Returns:
        Order ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{random_suffix}"


def amount_to_cents(amount: Union[float, Decimal]) -> int:
    """Convert amount to cents (smallest currency unit).
    
    Args:
        amount: Amount in major currency unit
    
    Returns:
        Amount in cents
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))
    
    return int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def cents_to_amount(cents: int) -> Decimal:
    """Convert cents to amount (major currency unit).
    
    Args:
        cents: Amount in cents
    
    Returns:
        Amount in major currency unit
    """
    return Decimal(cents) / 100


def clean_phone_number(phone: str) -> str:
    """Clean and format phone number.
    
    Args:
        phone: Phone number string
    
    Returns:
        Cleaned phone number
    """
    # Remove all non-numeric characters
    cleaned = ''.join(filter(str.isdigit, phone))
    
    # Remove country code if present (assuming Malaysia +60)
    if cleaned.startswith("60") and len(cleaned) > 10:
        cleaned = "0" + cleaned[2:]
    
    return cleaned


def validate_email(email: str) -> bool:
    """Basic email validation.
    
    Args:
        email: Email address
    
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%d-%m-%Y %H:%M:%S") -> datetime:
    """Parse datetime from string.
    
    Args:
        dt_str: Datetime string
        format_str: Format string (default matches ToyyibPay format)
    
    Returns:
        Datetime object
    """
    return datetime.strptime(dt_str, format_str)


def sanitize_alphanumeric(text: str, allow_space: bool = True, allow_underscore: bool = True) -> str:
    """Sanitize text to contain only alphanumeric characters.
    
    Args:
        text: Text to sanitize
        allow_space: Allow spaces
        allow_underscore: Allow underscores
    
    Returns:
        Sanitized text
    """
    allowed_chars = string.ascii_letters + string.digits
    if allow_space:
        allowed_chars += " "
    if allow_underscore:
        allowed_chars += "_"
    
    return ''.join(c for c in text if c in allowed_chars)


def dict_to_form_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Convert dictionary to form data format.
    
    Args:
        data: Dictionary to convert
    
    Returns:
        Form data dictionary with string values
    """
    form_data = {}
    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, bool):
            form_data[key] = "1" if value else "0"
        elif isinstance(value, (int, float, Decimal)):
            form_data[key] = str(value)
        else:
            form_data[key] = str(value)
    
    return form_data


def merge_dicts(base: Dict[str, Any], *others: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence.
    
    Args:
        base: Base dictionary
        *others: Other dictionaries to merge
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for other in others:
        if other:
            result.update(other)
    return result


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

