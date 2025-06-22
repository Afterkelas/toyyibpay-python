"""Tests for utility functions."""

from datetime import datetime
from decimal import Decimal

import pytest

from toyyibpay import utils


class TestULIDGeneration:
    """Test ULID generation."""
    
    @pytest.mark.unit
    def test_generate_ulid_format(self):
        """Test ULID format is correct."""
        ulid = utils.generate_ulid()
        
        assert len(ulid) == 26
        assert ulid.isalnum()
        assert ulid.isupper()
    
    @pytest.mark.unit
    def test_generate_ulid_uniqueness(self):
        """Test ULID uniqueness."""
        ulids = set()
        for _ in range(100):
            ulid = utils.generate_ulid()
            assert ulid not in ulids
            ulids.add(ulid)
    
    @pytest.mark.unit
    def test_generate_ulid_lexicographic_ordering(self):
        """Test ULIDs are lexicographically sortable by time."""
        import time
        
        ulid1 = utils.generate_ulid()
        time.sleep(0.01)  # Small delay
        ulid2 = utils.generate_ulid()
        
        assert ulid1 < ulid2  # Later ULID should be greater


class TestOrderIDGeneration:
    """Test order ID generation."""
    
    @pytest.mark.unit
    def test_generate_order_id_default_prefix(self):
        """Test order ID with default prefix."""
        order_id = utils.generate_order_id()
        
        assert order_id.startswith("ORD-")
        parts = order_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 14  # Timestamp
        assert len(parts[2]) == 6   # Random suffix
    
    @pytest.mark.unit
    def test_generate_order_id_custom_prefix(self):
        """Test order ID with custom prefix."""
        order_id = utils.generate_order_id(prefix="INV")
        
        assert order_id.startswith("INV-")
    
    @pytest.mark.unit
    def test_generate_order_id_uniqueness(self):
        """Test order ID uniqueness."""
        order_ids = set()
        for _ in range(100):
            order_id = utils.generate_order_id()
            assert order_id not in order_ids
            order_ids.add(order_id)


class TestAmountConversion:
    """Test amount conversion utilities."""
    
    @pytest.mark.unit
    def test_amount_to_cents_float(self):
        """Test converting float amount to cents."""
        assert utils.amount_to_cents(100.00) == 10000
        assert utils.amount_to_cents(99.99) == 9999
        assert utils.amount_to_cents(0.01) == 1
        assert utils.amount_to_cents(1234.56) == 123456
    
    @pytest.mark.unit
    def test_amount_to_cents_decimal(self):
        """Test converting Decimal amount to cents."""
        assert utils.amount_to_cents(Decimal("100.00")) == 10000
        assert utils.amount_to_cents(Decimal("99.99")) == 9999
        assert utils.amount_to_cents(Decimal("0.01")) == 1
    
    @pytest.mark.unit
    def test_amount_to_cents_rounding(self):
        """Test amount to cents with rounding."""
        # Should round half up
        assert utils.amount_to_cents(99.995) == 10000
        assert utils.amount_to_cents(99.994) == 9999
    
    @pytest.mark.unit
    def test_cents_to_amount(self):
        """Test converting cents to amount."""
        assert utils.cents_to_amount(10000) == Decimal("100.00")
        assert utils.cents_to_amount(9999) == Decimal("99.99")
        assert utils.cents_to_amount(1) == Decimal("0.01")
        assert utils.cents_to_amount(0) == Decimal("0.00")


class TestPhoneNumberCleaning:
    """Test phone number cleaning."""
    
    @pytest.mark.unit
    def test_clean_phone_number_basic(self):
        """Test basic phone number cleaning."""
        assert utils.clean_phone_number("0123456789") == "0123456789"
        assert utils.clean_phone_number("012-345-6789") == "0123456789"
        assert utils.clean_phone_number("012 345 6789") == "0123456789"
        assert utils.clean_phone_number("(012) 345-6789") == "0123456789"
    
    @pytest.mark.unit
    def test_clean_phone_number_country_code(self):
        """Test cleaning phone number with country code."""
        assert utils.clean_phone_number("60123456789") == "0123456789"
        assert utils.clean_phone_number("+60123456789") == "0123456789"
        assert utils.clean_phone_number("0060123456789") == "0123456789"
    
    @pytest.mark.unit
    def test_clean_phone_number_short(self):
        """Test cleaning short phone numbers."""
        assert utils.clean_phone_number("60123") == "60123"  # Too short, not modified
        assert utils.clean_phone_number("123456") == "123456"


class TestEmailValidation:
    """Test email validation."""
    
    @pytest.mark.unit
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        assert utils.validate_email("user@example.com") is True
        assert utils.validate_email("john.doe@company.co.uk") is True
        assert utils.validate_email("test+tag@domain.com") is True
        assert utils.validate_email("user123@sub.domain.com") is True
    
    @pytest.mark.unit
    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        assert utils.validate_email("invalid") is False
        assert utils.validate_email("@example.com") is False
        assert utils.validate_email("user@") is False
        assert utils.validate_email("user @example.com") is False
        assert utils.validate_email("user@exam ple.com") is False


class TestDateTimeUtils:
    """Test datetime utilities."""
    
    @pytest.mark.unit
    def test_format_datetime_default(self):
        """Test formatting datetime with default format."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        formatted = utils.format_datetime(dt)
        assert formatted == "2024-01-15 10:30:45"
    
    @pytest.mark.unit
    def test_format_datetime_custom(self):
        """Test formatting datetime with custom format."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        formatted = utils.format_datetime(dt, "%Y/%m/%d")
        assert formatted == "2024/01/15"
    
    @pytest.mark.unit
    def test_parse_datetime_default(self):
        """Test parsing datetime with default format."""
        dt_str = "15-01-2024 10:30:45"
        dt = utils.parse_datetime(dt_str)
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45
    
    @pytest.mark.unit
    def test_parse_datetime_custom(self):
        """Test parsing datetime with custom format."""
        dt_str = "2024/01/15"
        dt = utils.parse_datetime(dt_str, "%Y/%m/%d")
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15


class TestTextSanitization:
    """Test text sanitization."""
    
    @pytest.mark.unit
    def test_sanitize_alphanumeric_default(self):
        """Test sanitizing text with default settings."""
        assert utils.sanitize_alphanumeric("Hello World_123") == "Hello World_123"
        assert utils.sanitize_alphanumeric("Test@#$%123") == "Test123"
        assert utils.sanitize_alphanumeric("Special!@#Characters") == "SpecialCharacters"
    
    @pytest.mark.unit
    def test_sanitize_alphanumeric_no_space(self):
        """Test sanitizing text without allowing spaces."""
        result = utils.sanitize_alphanumeric("Hello World", allow_space=False)
        assert result == "HelloWorld"
    
    @pytest.mark.unit
    def test_sanitize_alphanumeric_no_underscore(self):
        """Test sanitizing text without allowing underscores."""
        result = utils.sanitize_alphanumeric("Hello_World", allow_underscore=False)
        assert result == "HelloWorld"
    
    @pytest.mark.unit
    def test_sanitize_alphanumeric_strict(self):
        """Test strict alphanumeric sanitization."""
        result = utils.sanitize_alphanumeric(
            "Hello_World 123!",
            allow_space=False,
            allow_underscore=False
        )
        assert result == "HelloWorld123"


class TestDictUtils:
    """Test dictionary utilities."""
    
    @pytest.mark.unit
    def test_dict_to_form_data(self):
        """Test converting dict to form data."""
        data = {
            "name": "John Doe",
            "age": 30,
            "amount": 99.99,
            "active": True,
            "inactive": False,
            "empty": None,
            "decimal": Decimal("100.50"),
        }
        
        form_data = utils.dict_to_form_data(data)
        
        assert form_data["name"] == "John Doe"
        assert form_data["age"] == "30"
        assert form_data["amount"] == "99.99"
        assert form_data["active"] == "1"
        assert form_data["inactive"] == "0"
        assert "empty" not in form_data  # None values excluded
        assert form_data["decimal"] == "100.50"
    
    @pytest.mark.unit
    def test_merge_dicts(self):
        """Test merging dictionaries."""
        base = {"a": 1, "b": 2}
        override1 = {"b": 3, "c": 4}
        override2 = {"c": 5, "d": 6}
        
        result = utils.merge_dicts(base, override1, override2)
        
        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}
        # Original should not be modified
        assert base == {"a": 1, "b": 2}
    
    @pytest.mark.unit
    def test_merge_dicts_with_none(self):
        """Test merging dictionaries with None values."""
        base = {"a": 1}
        result = utils.merge_dicts(base, None, {"b": 2})
        
        assert result == {"a": 1, "b": 2}


class TestStringUtils:
    """Test string utilities."""
    
    @pytest.mark.unit
    def test_truncate_string_short(self):
        """Test truncating string that's already short."""
        text = "Short text"
        result = utils.truncate_string(text, 20)
        assert result == "Short text"
    
    @pytest.mark.unit
    def test_truncate_string_long(self):
        """Test truncating long string."""
        text = "This is a very long text that needs to be truncated"
        result = utils.truncate_string(text, 20)
        assert result == "This is a very lo..."
        assert len(result) == 20
    
    @pytest.mark.unit
    def test_truncate_string_custom_suffix(self):
        """Test truncating with custom suffix."""
        text = "This is a long text"
        result = utils.truncate_string(text, 15, suffix=" [more]")
        assert result == "This is [more]"
    
    @pytest.mark.unit
    def test_truncate_string_exact_length(self):
        """Test truncating string at exact length."""
        text = "Exactly twenty chars"  # 20 characters
        result = utils.truncate_string(text, 20)
        assert result == "Exactly twenty chars"