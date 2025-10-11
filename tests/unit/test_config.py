"""Unit tests for SDK configuration.

Tests the SDKConfig class including validation, environment loading,
and configuration copying.
"""

import pytest

from permission_sdk import ConfigurationError, SDKConfig


class TestSDKConfig:
    """Tests for SDKConfig class."""

    def test_valid_config(self) -> None:
        """Test creating a valid configuration."""
        config = SDKConfig(
            base_url="https://api.example.com",
            api_key="test-key",
        )

        assert config.base_url == "https://api.example.com"
        assert config.api_key == "test-key"
        assert config.timeout == 30  # Default value
        assert config.max_retries == 3  # Default value

    def test_config_removes_trailing_slash(self) -> None:
        """Test that trailing slashes are removed from base_url."""
        config = SDKConfig(
            base_url="https://api.example.com/",
            api_key="test-key",
        )

        assert config.base_url == "https://api.example.com"

    def test_missing_base_url(self) -> None:
        """Test that missing base_url raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="base_url is required"):
            SDKConfig(
                base_url="",
                api_key="test-key",
            )

    def test_invalid_base_url_scheme(self) -> None:
        """Test that invalid URL scheme raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="must start with http"):
            SDKConfig(
                base_url="ftp://api.example.com",
                api_key="test-key",
            )

    def test_missing_api_key(self) -> None:
        """Test that missing API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="api_key is required"):
            SDKConfig(
                base_url="https://api.example.com",
                api_key="",
            )

    def test_negative_timeout(self) -> None:
        """Test that negative timeout raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="timeout must be positive"):
            SDKConfig(
                base_url="https://api.example.com",
                api_key="test-key",
                timeout=-1,
            )

    def test_negative_max_retries(self) -> None:
        """Test that negative max_retries raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="max_retries must be non-negative"):
            SDKConfig(
                base_url="https://api.example.com",
                api_key="test-key",
                max_retries=-1,
            )

    def test_invalid_retry_multiplier(self) -> None:
        """Test that retry_multiplier < 1 raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="retry_multiplier must be"):
            SDKConfig(
                base_url="https://api.example.com",
                api_key="test-key",
                retry_multiplier=0.5,
            )

    def test_config_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("PERMISSION_SDK_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("PERMISSION_SDK_API_KEY", "env-key")
        monkeypatch.setenv("PERMISSION_SDK_TIMEOUT", "60")
        monkeypatch.setenv("PERMISSION_SDK_MAX_RETRIES", "5")

        config = SDKConfig.from_env()

        assert config.base_url == "https://api.example.com"
        assert config.api_key == "env-key"
        assert config.timeout == 60
        assert config.max_retries == 5

    def test_config_from_env_missing_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing required env vars raises ConfigurationError."""
        # Clear any existing environment variables
        monkeypatch.delenv("PERMISSION_SDK_BASE_URL", raising=False)
        monkeypatch.delenv("PERMISSION_SDK_API_KEY", raising=False)

        with pytest.raises(ConfigurationError, match="BASE_URL is required"):
            SDKConfig.from_env()

    def test_config_from_env_with_custom_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config with custom environment variable prefix."""
        monkeypatch.setenv("CUSTOM_BASE_URL", "https://api.example.com")
        monkeypatch.setenv("CUSTOM_API_KEY", "custom-key")

        config = SDKConfig.from_env(prefix="CUSTOM_")

        assert config.base_url == "https://api.example.com"
        assert config.api_key == "custom-key"

    def test_config_copy(self) -> None:
        """Test copying configuration with changes."""
        original = SDKConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=30,
        )

        modified = original.copy(timeout=60, max_retries=5)

        # Original unchanged
        assert original.timeout == 30
        assert original.max_retries == 3

        # Modified has new values
        assert modified.timeout == 60
        assert modified.max_retries == 5
        assert modified.base_url == "https://api.example.com"  # Preserved
        assert modified.api_key == "test-key"  # Preserved

    def test_config_copy_preserves_retry_status_set(self) -> None:
        """Test that copy preserves the retry_on_status set."""
        original = SDKConfig(
            base_url="https://api.example.com",
            api_key="test-key",
        )

        modified = original.copy(timeout=60)

        # Both should have the same retry status codes
        assert modified.retry_on_status == original.retry_on_status
        # But they should be different sets (not same object)
        assert modified.retry_on_status is not original.retry_on_status
