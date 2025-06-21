"""Configuration for ToyyibPay SDK."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from .enums import Environment


@dataclass
class ToyyibPayConfig:
    """Configuration for ToyyibPay client."""

    api_key: str
    category_id: Optional[str] = None
    environment: Environment = Environment.PRODUCTION

    # URLs
    dev_base_url: str = "https://dev.toyyibpay.com"
    prod_base_url: str = "https://toyyibpay.com"

    # Payment URLs
    return_url: Optional[str] = None
    callback_url: Optional[str] = None

    # HTTP Client settings
    timeout: float = 30.0
    max_retries: int = 3
    verify_ssl: bool = True

    # Database settings (optional)
    database_url: Optional[str] = None

    # Additional headers
    additional_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("API key is required")

    @property
    def base_url(self) -> str:
        """Get base URL based on environment."""
        if self.environment == Environment.PRODUCTION:
            return self.prod_base_url
        return self.dev_base_url

    @property
    def api_base_url(self) -> str:
        """Get API base URL."""
        return f"{self.base_url}/index.php/api"

    @classmethod
    def from_env(cls, **kwargs: Any) -> "ToyyibPayConfig":
        """Create config from environment variables.

        Environment variables:
        - TOYYIBPAY_API_KEY: API key (required)
        - TOYYIBPAY_CATEGORY_ID: Default category ID
        - TOYYIBPAY_ENVIRONMENT: Environment (dev/staging/production)
        - TOYYIBPAY_RETURN_URL: Default return URL
        - TOYYIBPAY_CALLBACK_URL: Default callback URL
        - DATABASE_URL: PostgreSQL connection string
        """
        config_dict = {
            "api_key": os.getenv("TOYYIBPAY_API_KEY", ""),
            "category_id": os.getenv("TOYYIBPAY_CATEGORY_ID"),
            "environment": os.getenv("TOYYIBPAY_ENVIRONMENT", Environment.PRODUCTION),
            "return_url": os.getenv("TOYYIBPAY_RETURN_URL"),
            "callback_url": os.getenv("TOYYIBPAY_CALLBACK_URL"),
            "database_url": os.getenv("DATABASE_URL"),
        }

        # Override with any provided kwargs
        config_dict.update(kwargs)

        return cls(**config_dict)


# Global configuration instance
_global_config: Optional[ToyyibPayConfig] = None


def set_config(config: ToyyibPayConfig) -> None:
    """Set global configuration."""
    global _global_config
    _global_config = config


def get_config() -> ToyyibPayConfig:
    """Get global configuration."""
    if _global_config is None:
        raise RuntimeError(
            "ToyyibPay configuration not set. "
            "Call toyyibpay.set_config() or use ToyyibPayClient with explicit config."
        )
    return _global_config
