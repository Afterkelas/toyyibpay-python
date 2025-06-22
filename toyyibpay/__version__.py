"""Version information for ToyyibPay Python SDK."""

__title__ = "toyyibpay"
__description__ = "Official Python SDK for ToyyibPay Payment Gateway"
__url__ = "https://github.com/waizwafiq/toyyibpay-python"
__version__ = "0.1.1"
__version_info__ = tuple(int(i) for i in __version__.split("."))
__author__ = "Waiz Wafiq"
__author_email__ = "mwaizwafiq@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Waiz Wafiq"

# Development status
__status__ = "Planning"

# Supported Python versions
__python_requires__ = ">=3.8"

# API version compatibility
__api_version__ = "v1"
__min_toyyibpay_version__ = "1.0.0"

# Build information (can be updated during CI/CD)
__build__ = ""
__commit__ = ""
__branch__ = ""

# Feature flags
__features__ = {
    "async_support": True,
    "webhook_validation": True,
    "database_support": True,
    "retry_mechanism": False,  # Coming in next version
    "batch_operations": False,  # Coming in next version
}


def get_version() -> str:
    """Get the current version string.
    
    Returns:
        Version string, including build info if available.
    """
    version = __version__
    if __build__:
        version = f"{version}+{__build__}"
    return version


def get_user_agent() -> str:
    """Get the User-Agent string for HTTP requests.
    
    Returns:
        User-Agent string with version info.
    """
    return f"{__title__}/{__version__} Python"


def check_version(required_version: str) -> bool:
    """Check if current version meets the required version.
    
    Args:
        required_version: Minimum required version string
    
    Returns:
        True if current version >= required version
    """
    def parse_version(version: str) -> tuple:
        """Parse version string to tuple of integers."""
        return tuple(int(i) for i in version.split(".")[:3])
    
    current = parse_version(__version__)
    required = parse_version(required_version)
    
    return current >= required


# Version compatibility information
COMPATIBILITY = {
    "0.1.1": {
        "breaking_changes": [],
        "deprecations": [],
        "new_features": [
            "Initial release",
            "Synchronous client support",
            "Asynchronous client support",
            "PostgreSQL database integration",
            "Webhook handling",
            "Flask integration",
            "FastAPI integration",
        ],
    },
}


# All public API
__all__ = [
    "__title__",
    "__description__",
    "__url__",
    "__version__",
    "__version_info__",
    "__author__",
    "__author_email__",
    "__license__",
    "__copyright__",
    "__status__",
    "__python_requires__",
    "__api_version__",
    "__features__",
    "get_version",
    "get_user_agent",
    "check_version",
    "COMPATIBILITY",
]