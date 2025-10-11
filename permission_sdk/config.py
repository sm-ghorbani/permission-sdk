"""Configuration management for the Permission SDK.

This module provides configuration classes and utilities for SDK initialization.
"""

import os
from dataclasses import dataclass, field

from permission_sdk.exceptions import ConfigurationError


@dataclass
class SDKConfig:
    """SDK configuration with sensible defaults.

    This class holds all configuration needed to initialize the Permission SDK client.
    Configuration can be provided directly or loaded from environment variables.

    Attributes:
        base_url: Base URL of the Permission Service API
        api_key: API key for authentication
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_backoff: Initial backoff time between retries in seconds (default: 0.5)
        retry_multiplier: Backoff multiplier for exponential backoff (default: 2.0)
        retry_on_status: HTTP status codes that trigger a retry
        pool_maxsize: Maximum number of connections in the pool (default: 10)
        pool_connections: Number of connection pools to maintain (default: 10)
        validate_identifiers: Enable client-side identifier validation (default: True)

    Example:
        >>> config = SDKConfig(
        ...     base_url="https://permissions.example.com",
        ...     api_key="your-api-key",
        ...     timeout=60,
        ...     max_retries=5
        ... )
        >>> client = PermissionClient(config)

    Example (from environment):
        >>> config = SDKConfig.from_env()
        >>> client = PermissionClient(config)
    """

    # Connection settings
    base_url: str
    api_key: str
    timeout: int = 30

    # Retry configuration
    max_retries: int = 3
    retry_backoff: float = 0.5
    retry_multiplier: float = 2.0
    retry_on_status: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    # Connection pooling
    pool_maxsize: int = 10
    pool_connections: int = 10

    # Validation
    validate_identifiers: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If any configuration value is invalid
        """
        # Validate base_url
        if not self.base_url:
            raise ConfigurationError("base_url is required")

        if not self.base_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"base_url must start with http:// or https://, got: {self.base_url}"
            )

        # Remove trailing slash from base_url for consistency
        self.base_url = self.base_url.rstrip("/")

        # Validate api_key
        if not self.api_key:
            raise ConfigurationError("api_key is required")

        # Validate timeout
        if self.timeout <= 0:
            raise ConfigurationError(f"timeout must be positive, got: {self.timeout}")

        # Validate retry configuration
        if self.max_retries < 0:
            raise ConfigurationError(f"max_retries must be non-negative, got: {self.max_retries}")

        if self.retry_backoff < 0:
            raise ConfigurationError(
                f"retry_backoff must be non-negative, got: {self.retry_backoff}"
            )

        if self.retry_multiplier < 1:
            raise ConfigurationError(
                f"retry_multiplier must be >= 1, got: {self.retry_multiplier}",
            )

        # Validate pool settings
        if self.pool_maxsize <= 0:
            raise ConfigurationError(f"pool_maxsize must be positive, got: {self.pool_maxsize}")

        if self.pool_connections <= 0:
            raise ConfigurationError(
                f"pool_connections must be positive, got: {self.pool_connections}"
            )

    @classmethod
    def from_env(cls, prefix: str = "PERMISSION_SDK_") -> "SDKConfig":
        """Load configuration from environment variables.

        Environment variables:
            {prefix}BASE_URL: Base URL of the Permission Service
            {prefix}API_KEY: API key for authentication
            {prefix}TIMEOUT: Request timeout in seconds (optional)
            {prefix}MAX_RETRIES: Maximum retry attempts (optional)
            {prefix}RETRY_BACKOFF: Initial retry backoff in seconds (optional)
            {prefix}RETRY_MULTIPLIER: Retry backoff multiplier (optional)
            {prefix}POOL_MAXSIZE: Connection pool max size (optional)
            {prefix}POOL_CONNECTIONS: Number of connection pools (optional)
            {prefix}VALIDATE_IDENTIFIERS: Enable validation (optional, true/false)

        Args:
            prefix: Environment variable prefix (default: "PERMISSION_SDK_")

        Returns:
            SDKConfig instance with values from environment

        Raises:
            ConfigurationError: If required environment variables are missing

        Example:
            >>> # Export environment variables:
            >>> # export PERMISSION_SDK_BASE_URL=https://api.example.com
            >>> # export PERMISSION_SDK_API_KEY=secret-key
            >>> config = SDKConfig.from_env()
        """
        base_url = os.getenv(f"{prefix}BASE_URL")
        api_key = os.getenv(f"{prefix}API_KEY")

        if not base_url:
            raise ConfigurationError(f"Environment variable {prefix}BASE_URL is required")

        if not api_key:
            raise ConfigurationError(f"Environment variable {prefix}API_KEY is required")

        # Optional configuration with defaults
        timeout = int(os.getenv(f"{prefix}TIMEOUT", "30"))
        max_retries = int(os.getenv(f"{prefix}MAX_RETRIES", "3"))
        retry_backoff = float(os.getenv(f"{prefix}RETRY_BACKOFF", "0.5"))
        retry_multiplier = float(os.getenv(f"{prefix}RETRY_MULTIPLIER", "2.0"))
        pool_maxsize = int(os.getenv(f"{prefix}POOL_MAXSIZE", "10"))
        pool_connections = int(os.getenv(f"{prefix}POOL_CONNECTIONS", "10"))
        validate_identifiers = (
            os.getenv(
                f"{prefix}VALIDATE_IDENTIFIERS",
                "true",
            ).lower()
            == "true"
        )

        return cls(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
            retry_multiplier=retry_multiplier,
            pool_maxsize=pool_maxsize,
            pool_connections=pool_connections,
            validate_identifiers=validate_identifiers,
        )

    def copy(self, **changes: object) -> "SDKConfig":
        """Create a copy of this config with specified changes.

        Args:
            **changes: Configuration fields to override

        Returns:
            New SDKConfig instance with changes applied

        Example:
            >>> config = SDKConfig(base_url="https://api.example.com", api_key="key")
            >>> dev_config = config.copy(timeout=120, max_retries=5)
        """
        current = {
            "base_url": self.base_url,
            "api_key": self.api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_backoff": self.retry_backoff,
            "retry_multiplier": self.retry_multiplier,
            "retry_on_status": self.retry_on_status.copy(),
            "pool_maxsize": self.pool_maxsize,
            "pool_connections": self.pool_connections,
            "validate_identifiers": self.validate_identifiers,
        }
        current.update(changes)
        return SDKConfig(**current)  # type: ignore
