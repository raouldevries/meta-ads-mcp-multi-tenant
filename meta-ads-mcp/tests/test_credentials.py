"""
Tests for multi-tenant credential management.
"""

import json
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from meta_ads_mcp.core.credentials import (
    CredentialManager,
    get_credential_manager,
    ApiKeyConfig,
    AccountConfig,
    AccountNotFoundError,
    KeyNotFoundError,
    TokenExpiredError,
    ValidationError,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    CredentialManager.reset_instance()
    yield
    CredentialManager.reset_instance()


@pytest.fixture
def valid_credentials():
    """Valid credentials.json data."""
    return {
        "version": 2,
        "api_keys": {
            "key1": {
                "access_token": "token_abc_123",
                "business_manager_id": "bm_123",
                "app_id": "app_123",
                "tier": "standard"
            },
            "key2": {
                "access_token": "token_def_456",
                "business_manager_id": "bm_456",
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "tier": "development"
            }
        },
        "accounts": {
            "account1": {
                "display_name": "Test Account 1",
                "ad_account_id": "act_111111",
                "api_key": "key1"
            },
            "account2": {
                "display_name": "Test Account 2",
                "ad_account_id": "act_222222",
                "api_key": "key2"
            }
        },
        "default_account": "account1"
    }


class TestApiKeyConfig:
    """Tests for ApiKeyConfig dataclass."""

    def test_is_expired_no_expiry(self):
        """Token without expiry is never expired."""
        key = ApiKeyConfig(
            name="test",
            access_token="token",
            business_manager_id="bm_123"
        )
        assert not key.is_expired

    def test_is_expired_future(self):
        """Token with future expiry is not expired."""
        key = ApiKeyConfig(
            name="test",
            access_token="token",
            business_manager_id="bm_123",
            expires_at=datetime.now() + timedelta(days=30)
        )
        assert not key.is_expired

    def test_is_expired_past(self):
        """Token with past expiry is expired."""
        key = ApiKeyConfig(
            name="test",
            access_token="token",
            business_manager_id="bm_123",
            expires_at=datetime.now() - timedelta(days=1)
        )
        assert key.is_expired

    def test_days_until_expiry_no_expiry(self):
        """Token without expiry returns None."""
        key = ApiKeyConfig(
            name="test",
            access_token="token",
            business_manager_id="bm_123"
        )
        assert key.days_until_expiry is None

    def test_days_until_expiry_future(self):
        """Token with future expiry returns positive days."""
        key = ApiKeyConfig(
            name="test",
            access_token="token",
            business_manager_id="bm_123",
            expires_at=datetime.now() + timedelta(days=30)
        )
        assert key.days_until_expiry >= 29  # Allow for time passing


class TestCredentialManagerSingleton:
    """Tests for singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Multiple calls return same instance."""
        with patch.object(CredentialManager, '_load_credentials'):
            manager1 = CredentialManager()
            manager2 = CredentialManager()
            assert manager1 is manager2

    def test_reset_instance_creates_new(self):
        """reset_instance allows creating new instance."""
        with patch.object(CredentialManager, '_load_credentials'):
            manager1 = CredentialManager()
            CredentialManager.reset_instance()
            manager2 = CredentialManager()
            assert manager1 is not manager2

    def test_get_credential_manager_returns_singleton(self):
        """get_credential_manager() returns singleton."""
        with patch.object(CredentialManager, '_load_credentials'):
            manager1 = get_credential_manager()
            manager2 = get_credential_manager()
            assert manager1 is manager2


class TestCredentialManagerLoading:
    """Tests for credential loading."""

    def test_load_from_json(self, valid_credentials, tmp_path):
        """Load credentials from JSON file."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        assert len(manager.api_keys) == 2
        assert len(manager.accounts) == 2
        assert manager.default_account == "account1"
        assert manager._state.current_account == "account1"

    def test_load_from_env(self):
        """Load credentials from environment variables."""
        env_vars = {
            "META_ACCESS_TOKEN": "env_token_123",
            "META_AD_ACCOUNT_ID": "act_env_123",
            "META_APP_ID": "app_env_123"
        }

        with patch.dict(os.environ, env_vars, clear=False):
            with patch.object(
                CredentialManager, '_get_credentials_path',
                return_value=Path("/nonexistent/path")
            ):
                manager = CredentialManager()

        assert len(manager.api_keys) == 1
        assert "default" in manager.api_keys
        assert manager.api_keys["default"].access_token == "env_token_123"
        assert len(manager.accounts) == 1
        assert manager.accounts["default"].ad_account_id == "act_env_123"

    def test_load_invalid_version(self, tmp_path):
        """Raise error for invalid version."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps({"version": 1}))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            with pytest.raises(ValidationError, match="Unsupported credentials version"):
                CredentialManager()

    def test_load_invalid_api_key_reference(self, valid_credentials, tmp_path):
        """Raise error when account references non-existent key."""
        valid_credentials["accounts"]["account1"]["api_key"] = "nonexistent"
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            with pytest.raises(ValidationError, match="references unknown api_key"):
                CredentialManager()

    def test_load_invalid_default_account(self, valid_credentials, tmp_path):
        """Raise error when default_account doesn't exist."""
        valid_credentials["default_account"] = "nonexistent"
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            with pytest.raises(ValidationError, match="default_account.*not found"):
                CredentialManager()

    def test_load_duplicate_tokens(self, valid_credentials, tmp_path):
        """Raise error for duplicate access tokens."""
        valid_credentials["api_keys"]["key2"]["access_token"] = \
            valid_credentials["api_keys"]["key1"]["access_token"]
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            with pytest.raises(ValidationError, match="Duplicate access_token"):
                CredentialManager()

    def test_load_duplicate_account_ids(self, valid_credentials, tmp_path):
        """Raise error for duplicate ad account IDs."""
        valid_credentials["accounts"]["account2"]["ad_account_id"] = \
            valid_credentials["accounts"]["account1"]["ad_account_id"]
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            with pytest.raises(ValidationError, match="Duplicate ad_account_id"):
                CredentialManager()


class TestTokenRouting:
    """Tests for token routing."""

    @pytest.fixture
    def manager_with_accounts(self, valid_credentials, tmp_path):
        """Create manager with loaded credentials."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            return CredentialManager()

    def test_get_token_for_current_account(self, manager_with_accounts):
        """Get token for current account."""
        token = manager_with_accounts.get_token_for_account()
        assert token == "token_abc_123"

    def test_get_token_for_named_account(self, manager_with_accounts):
        """Get token for specific account."""
        token = manager_with_accounts.get_token_for_account("account2")
        assert token == "token_def_456"

    def test_get_token_account_not_found(self, manager_with_accounts):
        """Raise error for non-existent account."""
        with pytest.raises(AccountNotFoundError, match="Account 'nonexistent' not found"):
            manager_with_accounts.get_token_for_account("nonexistent")

    def test_get_token_no_current_account(self, tmp_path):
        """Raise error when no current account set."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps({
            "version": 2,
            "api_keys": {},
            "accounts": {}
        }))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        with pytest.raises(AccountNotFoundError, match="no default account set"):
            manager.get_token_for_account()

    def test_get_token_expired(self, tmp_path):
        """Raise error for expired token."""
        creds = {
            "version": 2,
            "api_keys": {
                "expired_key": {
                    "access_token": "expired_token",
                    "business_manager_id": "bm",
                    "expires_at": (datetime.now() - timedelta(days=1)).isoformat()
                }
            },
            "accounts": {
                "test": {
                    "display_name": "Test",
                    "ad_account_id": "act_123",
                    "api_key": "expired_key"
                }
            },
            "default_account": "test"
        }
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(creds))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        with pytest.raises(TokenExpiredError, match="expired"):
            manager.get_token_for_account()

    def test_get_account_id(self, manager_with_accounts):
        """Get account ID for current account."""
        account_id = manager_with_accounts.get_account_id()
        assert account_id == "act_111111"

    def test_get_account_id_named(self, manager_with_accounts):
        """Get account ID for named account."""
        account_id = manager_with_accounts.get_account_id("account2")
        assert account_id == "act_222222"

    def test_get_key_for_account(self, manager_with_accounts):
        """Get API key config for account."""
        key = manager_with_accounts.get_key_for_account("account1")
        assert key.name == "key1"
        assert key.tier == "standard"


class TestAccountManagement:
    """Tests for account management."""

    @pytest.fixture
    def manager_with_accounts(self, valid_credentials, tmp_path):
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(valid_credentials))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            return CredentialManager()

    def test_get_current_account(self, manager_with_accounts):
        """Get current account name."""
        assert manager_with_accounts.get_current_account() == "account1"

    def test_set_current_account_success(self, manager_with_accounts):
        """Successfully switch account."""
        result = manager_with_accounts.set_current_account("account2")
        assert result is True
        assert manager_with_accounts.get_current_account() == "account2"

    def test_set_current_account_not_found(self, manager_with_accounts):
        """Return False for non-existent account."""
        result = manager_with_accounts.set_current_account("nonexistent")
        assert result is False
        assert manager_with_accounts.get_current_account() == "account1"

    def test_list_accounts(self, manager_with_accounts):
        """List all accounts with metadata."""
        accounts = manager_with_accounts.list_accounts()
        assert len(accounts) == 2

        acc1 = next(a for a in accounts if a["name"] == "account1")
        assert acc1["display_name"] == "Test Account 1"
        assert acc1["ad_account_id"] == "act_111111"
        assert acc1["api_key"] == "key1"
        assert acc1["is_current"] is True

    def test_list_api_keys(self, manager_with_accounts):
        """List all API keys with metadata."""
        keys = manager_with_accounts.list_api_keys()
        assert len(keys) == 2

        key1 = next(k for k in keys if k["name"] == "key1")
        assert key1["tier"] == "standard"
        assert "account1" in key1["accounts"]


class TestTokenExpirationMonitoring:
    """Tests for token expiration monitoring."""

    def test_get_expiring_tokens_none(self, tmp_path):
        """Return empty list when no tokens expiring."""
        creds = {
            "version": 2,
            "api_keys": {
                "key1": {
                    "access_token": "token1",
                    "business_manager_id": "bm",
                    "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
                }
            },
            "accounts": {
                "test": {
                    "display_name": "Test",
                    "ad_account_id": "act_123",
                    "api_key": "key1"
                }
            }
        }
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(creds))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        expiring = manager.get_expiring_tokens(days_threshold=7)
        assert expiring == []

    def test_get_expiring_tokens_found(self, tmp_path):
        """Return tokens expiring within threshold."""
        creds = {
            "version": 2,
            "api_keys": {
                "expiring_key": {
                    "access_token": "token1",
                    "business_manager_id": "bm",
                    "expires_at": (datetime.now() + timedelta(days=3)).isoformat()
                }
            },
            "accounts": {
                "test": {
                    "display_name": "Test",
                    "ad_account_id": "act_123",
                    "api_key": "expiring_key"
                }
            }
        }
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(creds))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        expiring = manager.get_expiring_tokens(days_threshold=7)
        assert len(expiring) == 1
        assert expiring[0]["key_name"] == "expiring_key"
        assert "test" in expiring[0]["accounts_affected"]

    def test_check_token_expiration_alerts_none(self, tmp_path):
        """Return None when no tokens expiring."""
        creds = {
            "version": 2,
            "api_keys": {
                "key1": {
                    "access_token": "token1",
                    "business_manager_id": "bm"
                    # No expiration
                }
            },
            "accounts": {}
        }
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(creds))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        alert = manager.check_token_expiration_alerts()
        assert alert is None

    def test_check_token_expiration_alerts_warning(self, tmp_path):
        """Return warning for expiring tokens."""
        creds = {
            "version": 2,
            "api_keys": {
                "expiring_key": {
                    "access_token": "token1",
                    "business_manager_id": "bm",
                    "expires_at": (datetime.now() + timedelta(days=3)).isoformat()
                }
            },
            "accounts": {
                "test": {
                    "display_name": "Test",
                    "ad_account_id": "act_123",
                    "api_key": "expiring_key"
                }
            }
        }
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text(json.dumps(creds))

        with patch.object(
            CredentialManager, '_get_credentials_path', return_value=cred_file
        ):
            manager = CredentialManager()

        alert = manager.check_token_expiration_alerts()
        assert alert is not None
        assert "WARNING" in alert
        assert "expiring_key" in alert


class TestPlatformPaths:
    """Tests for platform-specific path resolution."""

    def test_macos_path(self):
        """Test macOS credentials path."""
        with patch('platform.system', return_value='Darwin'):
            with patch.object(CredentialManager, '_load_credentials'):
                manager = CredentialManager()
                path = manager._get_credentials_path()
                assert "Library/Application Support" in str(path)
                assert "meta-ads-mcp/credentials.json" in str(path)

    def test_windows_path(self):
        """Test Windows credentials path."""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData'}):
                with patch.object(CredentialManager, '_load_credentials'):
                    manager = CredentialManager()
                    path = manager._get_credentials_path()
                    assert "AppData" in str(path)

    def test_linux_path(self):
        """Test Linux credentials path."""
        with patch('platform.system', return_value='Linux'):
            with patch.object(CredentialManager, '_load_credentials'):
                manager = CredentialManager()
                path = manager._get_credentials_path()
                assert ".config" in str(path)
