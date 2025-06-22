"""Tests for configuration."""

import os
from dataclasses import FrozenInstanceError

import pytest

from toyyibpay.config import ToyyibPayConfig, set_config, get_config
from toyyibpay.enums import Environment


class TestToyyibPayConfig:
    """Test ToyyibPay configuration."""
    
    @pytest.mark.unit
    def test_config_initialization_minimal(self):
        """Test minimal configuration initialization."""
        config = ToyyibPayConfig(api_key="test-key")
        
        assert config.api_key == "test-key"
        assert config.category_id is None
        assert config.environment == Environment.PRODUCTION
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.verify_ssl is True
    
    @pytest.mark.unit
    def test_config_initialization_full(self):
        """Test full configuration initialization."""
        config = ToyyibPayConfig(
            api_key="test-key",
            category_id="CAT123",
            environment=Environment.DEV,
            dev_base_url="https://custom-dev.toyyibpay.com",
            prod_base_url="https://custom.toyyibpay.com",
            return_url="https://example.com/return",
            callback_url="https://example.com/callback",
            timeout=60.0,
            max_retries=5,
            verify_ssl=False,
            database_url="postgresql://user:pass@localhost/db",
            additional_headers={"X-Custom": "header"},
        )
        
        assert config.api_key == "test-key"
        assert config.category_id == "CAT123"
        assert config.environment == Environment.DEV
        assert config.timeout == 60.0
        assert config.additional_headers["X-Custom"] == "header"
    
    @pytest.mark.unit
    def test_config_validation_no_api_key(self):
        """Test configuration validation without API key."""
        with pytest.raises(ValueError, match="API key is required"):
            ToyyibPayConfig(api_key="")
        
        with pytest.raises(ValueError, match="API key is required"):
            ToyyibPayConfig(api_key=None)
    
    @pytest.mark.unit
    def test_config_base_url_production(self):
        """Test base URL for production environment."""
        config = ToyyibPayConfig(
            api_key="test-key",
            environment=Environment.PRODUCTION
        )
        
        assert config.base_url == "https://toyyibpay.com"
        assert config.api_base_url == "https://toyyibpay.com/index.php/api"
    
    @pytest.mark.unit
    def test_config_base_url_dev(self):
        """Test base URL for dev environment."""
        config = ToyyibPayConfig(
            api_key="test-key",
            environment=Environment.DEV
        )
        
        assert config.base_url == "https://dev.toyyibpay.com"
        assert config.api_base_url == "https://dev.toyyibpay.com/index.php/api"
    
    @pytest.mark.unit
    def test_config_base_url_staging(self):
        """Test base URL for staging environment."""
        config = ToyyibPayConfig(
            api_key="test-key",
            environment=Environment.STAGING
        )
        
        # Staging should use dev URL
        assert config.base_url == "https://dev.toyyibpay.com"
    
    @pytest.mark.unit
    def test_config_from_env_all_vars(self, env_vars):
        """Test creating config from environment variables."""
        config = ToyyibPayConfig.from_env()
        
        assert config.api_key == env_vars["TOYYIBPAY_API_KEY"]
        assert config.category_id == env_vars["TOYYIBPAY_CATEGORY_ID"]
        assert config.environment == env_vars["TOYYIBPAY_ENVIRONMENT"]
        assert config.return_url == env_vars["TOYYIBPAY_RETURN_URL"]
        assert config.callback_url == env_vars["TOYYIBPAY_CALLBACK_URL"]
        assert config.database_url == env_vars["DATABASE_URL"]
    
    @pytest.mark.unit
    def test_config_from_env_minimal(self, monkeypatch):
        """Test creating config from minimal environment variables."""
        monkeypatch.setenv("TOYYIBPAY_API_KEY", "env-api-key")
        
        config = ToyyibPayConfig.from_env()
        
        assert config.api_key == "env-api-key"
        assert config.category_id is None
        assert config.environment == Environment.PRODUCTION  # Default
    
    @pytest.mark.unit
    def test_config_from_env_with_overrides(self, env_vars):
        """Test creating config from env with overrides."""
        config = ToyyibPayConfig.from_env(
            api_key="override-key",
            timeout=45.0
        )
        
        assert config.api_key == "override-key"  # Override takes precedence
        assert config.category_id == env_vars["TOYYIBPAY_CATEGORY_ID"]  # From env
        assert config.timeout == 45.0  # Override
    
    @pytest.mark.unit
    def test_config_immutability(self):
        """Test configuration is immutable after creation."""
        config = ToyyibPayConfig(api_key="test-key")
        
        # Dataclass should prevent modification
        with pytest.raises(FrozenInstanceError):
            config.api_key = "new-key"


class TestGlobalConfig:
    """Test global configuration management."""
    
    @pytest.mark.unit
    def test_set_and_get_config(self):
        """Test setting and getting global config."""
        config = ToyyibPayConfig(api_key="global-key")
        set_config(config)
        
        retrieved = get_config()
        assert retrieved == config
        assert retrieved.api_key == "global-key"
    
    @pytest.mark.unit
    def test_get_config_not_set(self):
        """Test getting config when not set raises error."""
        # Reset is handled by fixture
        with pytest.raises(RuntimeError, match="configuration not set"):
            get_config()
    
    @pytest.mark.unit
    def test_set_config_overwrite(self):
        """Test overwriting global config."""
        config1 = ToyyibPayConfig(api_key="key1")
        config2 = ToyyibPayConfig(api_key="key2")
        
        set_config(config1)
        assert get_config().api_key == "key1"
        
        set_config(config2)
        assert get_config().api_key == "key2"


class TestConfigurationIntegration:
    """Test configuration integration with other components."""
    
    @pytest.mark.unit
    def test_config_with_client(self):
        """Test configuration with client initialization."""
        import toyyibpay
        
        # Set global config
        config = ToyyibPayConfig(api_key="integration-key")
        toyyibpay.set_config(config)
        
        # Client should use global config
        client = toyyibpay.Client()
        assert client.config.api_key == "integration-key"
    
    @pytest.mark.unit
    def test_config_environment_string_conversion(self):
        """Test environment string conversion."""
        # Environment enum should handle string values
        config = ToyyibPayConfig(
            api_key="test-key",
            environment="dev"  # String should work
        )
        assert config.environment == "dev"
        assert config.base_url == "https://dev.toyyibpay.com"