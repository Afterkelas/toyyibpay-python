"""Tests for version information."""

import re

import pytest

import toyyibpay
from toyyibpay.__version__ import (
    __version__,
    __version_info__,
    __title__,
    __description__,
    __author__,
    __python_requires__,
    __features__,
    get_version,
    get_user_agent,
    check_version,
    COMPATIBILITY,
)


class TestVersionInfo:
    """Test version information."""
    
    @pytest.mark.unit
    def test_version_format(self):
        """Test version follows semantic versioning."""
        # Check format X.Y.Z
        pattern = r'^\d+\.\d+\.\d+$'
        assert re.match(pattern, __version__)
    
    @pytest.mark.unit
    def test_version_info_tuple(self):
        """Test version info tuple matches version string."""
        version_parts = __version__.split('.')
        assert len(__version_info__) == 3
        assert __version_info__ == tuple(int(p) for p in version_parts)
    
    @pytest.mark.unit
    def test_package_metadata(self):
        """Test package metadata is defined."""
        assert __title__ == "toyyibpay"
        assert __description__
        assert __author__
        assert __python_requires__ == ">=3.8"
    
    @pytest.mark.unit
    def test_get_version_no_build(self):
        """Test get_version without build info."""
        version = get_version()
        assert version == __version__
    
    @pytest.mark.unit
    def test_get_version_with_build(self, monkeypatch):
        """Test get_version with build info."""
        monkeypatch.setattr('toyyibpay.__version__.__build__', 'abc123')
        version = get_version()
        assert version == f"{__version__}+abc123"
    
    @pytest.mark.unit
    def test_get_user_agent(self):
        """Test user agent string generation."""
        user_agent = get_user_agent()
        assert user_agent == f"toyyibpay/{__version__} Python"
    
    @pytest.mark.unit
    def test_check_version_equal(self):
        """Test version check with equal version."""
        assert check_version(__version__) is True
    
    @pytest.mark.unit
    def test_check_version_older(self):
        """Test version check with older required version."""
        assert check_version("0.0.1") is True
        assert check_version("0.0.9") is True
    
    @pytest.mark.unit
    def test_check_version_newer(self):
        """Test version check with newer required version."""
        assert check_version("99.0.0") is False
        assert check_version("1.0.0") is False  # Assuming current is 0.1.1
    
    @pytest.mark.unit
    def test_check_version_components(self):
        """Test version check handles different component comparisons."""
        # Assuming current version is 0.1.1
        assert check_version("0.0.9") is True   # Lower major
        assert check_version("0.1.1") is True   # Equal
        assert check_version("0.1.1") is False  # Higher patch
        assert check_version("0.2.0") is False  # Higher minor
        assert check_version("1.0.0") is False  # Higher major
    
    @pytest.mark.unit
    def test_features_dict(self):
        """Test features dictionary is properly defined."""
        assert isinstance(__features__, dict)
        assert "async_support" in __features__
        assert "webhook_validation" in __features__
        assert "database_support" in __features__
        
        # Check feature flags
        assert __features__["async_support"] is True
        assert __features__["webhook_validation"] is True
        assert __features__["database_support"] is True
    
    @pytest.mark.unit
    def test_compatibility_info(self):
        """Test compatibility information structure."""
        assert __version__ in COMPATIBILITY
        version_info = COMPATIBILITY[__version__]
        
        assert "breaking_changes" in version_info
        assert "deprecations" in version_info
        assert "new_features" in version_info
        
        assert isinstance(version_info["new_features"], list)
        assert len(version_info["new_features"]) > 0
    
    @pytest.mark.unit
    def test_version_imported_in_main_module(self):
        """Test version is accessible from main module."""
        assert hasattr(toyyibpay, '__version__')
        assert toyyibpay.__version__ == __version__
        
        # Test other imports
        assert hasattr(toyyibpay, 'get_version')
        assert hasattr(toyyibpay, 'get_user_agent')
        assert hasattr(toyyibpay, 'check_version')
    
    @pytest.mark.unit
    def test_version_consistency(self):
        """Test version is consistent across the package."""
        # Check version in main module matches
        assert toyyibpay.__version__ == __version__
        
        # Check user agent uses correct version
        assert __version__ in get_user_agent()
    
    @pytest.mark.unit
    def test_parse_version_edge_cases(self):
        """Test version parsing handles edge cases."""
        # Test with version strings of different lengths
        assert check_version("0") is True      # Should handle single digit
        assert check_version("0.1") is True    # Should handle two components
        assert check_version("0.1.1") is True  # Should handle three components
        
        # Very long version should be truncated to first 3 parts
        assert check_version("0.0.0.0.0") is True