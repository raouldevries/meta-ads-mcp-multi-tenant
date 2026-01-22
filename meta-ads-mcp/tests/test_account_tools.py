"""
Tests for MCP account management tools.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from meta_ads_mcp.core.account_tools import (
    list_configured_accounts,
    switch_account,
    get_current_account,
    get_rate_limit_status,
    validate_credentials,
    get_token_expiration_status,
)
from meta_ads_mcp.core.credentials import (
    CredentialManager,
    ApiKeyConfig,
    AccountConfig,
)
from meta_ads_mcp.core.rate_limiter import RateLimiter


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons before each test."""
    CredentialManager.reset_instance()
    RateLimiter.reset_instance()
    yield
    CredentialManager.reset_instance()
    RateLimiter.reset_instance()


@pytest.fixture
def mock_credential_manager():
    """Create mock credential manager with test data."""
    manager = MagicMock(spec=CredentialManager)

    # Set up API keys
    manager.api_keys = {
        "key1": ApiKeyConfig(
            name="key1",
            access_token="token_abc",
            business_manager_id="bm_123",
            tier="standard",
            expires_at=datetime.now() + timedelta(days=30)
        ),
        "key2": ApiKeyConfig(
            name="key2",
            access_token="token_def",
            business_manager_id="bm_456",
            tier="development",
            expires_at=datetime.now() + timedelta(days=5)  # Expiring soon
        )
    }

    # Set up accounts
    manager.accounts = {
        "account1": AccountConfig(
            name="account1",
            display_name="Test Account 1",
            ad_account_id="act_111111",
            api_key="key1"
        ),
        "account2": AccountConfig(
            name="account2",
            display_name="Test Account 2",
            ad_account_id="act_222222",
            api_key="key2"
        )
    }

    # Set up methods
    manager.get_current_account.return_value = "account1"
    manager.list_accounts.return_value = [
        {
            "name": "account1",
            "display_name": "Test Account 1",
            "ad_account_id": "act_111111",
            "api_key": "key1",
            "key_tier": "standard",
            "key_expires_in_days": 30,
            "is_current": True
        },
        {
            "name": "account2",
            "display_name": "Test Account 2",
            "ad_account_id": "act_222222",
            "api_key": "key2",
            "key_tier": "development",
            "key_expires_in_days": 5,
            "is_current": False
        }
    ]
    manager.list_api_keys.return_value = [
        {
            "name": "key1",
            "business_manager_id": "bm_123",
            "tier": "standard",
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
            "days_until_expiry": 30,
            "is_expired": False,
            "accounts": ["account1"]
        },
        {
            "name": "key2",
            "business_manager_id": "bm_456",
            "tier": "development",
            "expires_at": (datetime.now() + timedelta(days=5)).isoformat(),
            "days_until_expiry": 5,
            "is_expired": False,
            "accounts": ["account2"]
        }
    ]
    manager.check_token_expiration_alerts.return_value = (
        "WARNING: Token 'key2' expires in 5 days. Accounts affected: account2"
    )
    manager.get_expiring_tokens.return_value = [
        {
            "key_name": "key2",
            "expires_at": (datetime.now() + timedelta(days=5)).isoformat(),
            "days_remaining": 5,
            "accounts_affected": ["account2"]
        }
    ]
    manager.get_key_for_account.return_value = manager.api_keys["key1"]

    return manager


class TestListConfiguredAccounts:
    """Tests for list_configured_accounts tool."""

    @pytest.mark.asyncio
    async def test_returns_json(self, mock_credential_manager):
        """Returns valid JSON string."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await list_configured_accounts()

        # Should be valid JSON
        data = json.loads(result)
        assert "total_accounts" in data
        assert "accounts" in data

    @pytest.mark.asyncio
    async def test_includes_account_count(self, mock_credential_manager):
        """Result includes total account count."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await list_configured_accounts()

        data = json.loads(result)
        assert data["total_accounts"] == 2

    @pytest.mark.asyncio
    async def test_includes_current_account(self, mock_credential_manager):
        """Result includes current account name."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await list_configured_accounts()

        data = json.loads(result)
        assert data["current_account"] == "account1"

    @pytest.mark.asyncio
    async def test_includes_expiration_alert(self, mock_credential_manager):
        """Result includes token expiration alert."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await list_configured_accounts()

        data = json.loads(result)
        assert "token_expiration_alert" in data
        assert "key2" in data["token_expiration_alert"]

    @pytest.mark.asyncio
    async def test_includes_api_keys(self, mock_credential_manager):
        """Result includes API keys info."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await list_configured_accounts()

        data = json.loads(result)
        assert "api_keys" in data
        assert len(data["api_keys"]) == 2


class TestSwitchAccount:
    """Tests for switch_account tool."""

    @pytest.mark.asyncio
    async def test_switch_success(self, mock_credential_manager):
        """Successfully switch to valid account."""
        mock_credential_manager.set_current_account.return_value = True

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await switch_account("account2")

        data = json.loads(result)
        assert data["success"] is True
        assert data["current_account"] == "account2"

    @pytest.mark.asyncio
    async def test_switch_not_found(self, mock_credential_manager):
        """Return error for non-existent account."""
        mock_credential_manager.set_current_account.return_value = False

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await switch_account("nonexistent")

        data = json.loads(result)
        assert data["success"] is False
        assert "not found" in data["error"]
        assert "available_accounts" in data


class TestGetCurrentAccount:
    """Tests for get_current_account tool."""

    @pytest.mark.asyncio
    async def test_returns_current_account(self, mock_credential_manager):
        """Returns current account details."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await get_current_account()

        data = json.loads(result)
        assert data["account_name"] == "account1"
        assert data["display_name"] == "Test Account 1"
        assert data["ad_account_id"] == "act_111111"

    @pytest.mark.asyncio
    async def test_no_account_configured(self):
        """Return error when no account configured."""
        mock_manager = MagicMock(spec=CredentialManager)
        mock_manager.get_current_account.return_value = None
        mock_manager.accounts = {}

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_manager
        ):
            result = await get_current_account()

        data = json.loads(result)
        assert "error" in data
        assert "No account configured" in data["error"]


class TestGetRateLimitStatus:
    """Tests for get_rate_limit_status tool."""

    @pytest.mark.asyncio
    async def test_returns_status(self, mock_credential_manager):
        """Returns rate limit status for all keys."""
        mock_rate_limiter = MagicMock(spec=RateLimiter)
        mock_rate_limiter.get_all_status.return_value = {
            "key1": {
                "key_name": "key1",
                "status": "ok",
                "current_score": 10,
                "max_score": 9000
            }
        }

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            with patch(
                'meta_ads_mcp.core.account_tools.get_rate_limiter',
                return_value=mock_rate_limiter
            ):
                result = await get_rate_limit_status()

        data = json.loads(result)
        assert "rate_limits" in data
        assert "total_keys" in data

    @pytest.mark.asyncio
    async def test_includes_idle_keys(self, mock_credential_manager):
        """Includes keys that haven't been used yet."""
        mock_rate_limiter = MagicMock(spec=RateLimiter)
        mock_rate_limiter.get_all_status.return_value = {}  # No tracked keys

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            with patch(
                'meta_ads_mcp.core.account_tools.get_rate_limiter',
                return_value=mock_rate_limiter
            ):
                result = await get_rate_limit_status()

        data = json.loads(result)
        # Should include idle keys from credential manager
        assert data["total_keys"] == 2


class TestValidateCredentials:
    """Tests for validate_credentials tool."""

    @pytest.mark.asyncio
    async def test_no_accounts_configured(self):
        """Return error when no accounts configured."""
        mock_manager = MagicMock(spec=CredentialManager)
        mock_manager.accounts = {}

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_manager
        ):
            result = await validate_credentials()

        data = json.loads(result)
        assert "error" in data
        assert "No accounts configured" in data["error"]

    @pytest.mark.asyncio
    async def test_validation_success(self, mock_credential_manager):
        """Returns validation results."""
        from meta_ads_mcp.core.preflight import PreflightResult, PreflightStatus

        mock_result = PreflightResult(
            status=PreflightStatus.PASSED,
            keys=[],
            accounts=[],
            warnings=[],
            errors=[]
        )

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            with patch(
                'meta_ads_mcp.core.account_tools.run_preflight_checks',
                return_value=mock_result
            ):
                with patch(
                    'meta_ads_mcp.core.account_tools.format_preflight_result',
                    return_value="[PASSED] Preflight Check"
                ):
                    result = await validate_credentials()

        data = json.loads(result)
        assert data["status"] == "passed"
        assert data["passed"] is True

    @pytest.mark.asyncio
    async def test_validation_exception(self, mock_credential_manager):
        """Handle validation exception gracefully."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            with patch(
                'meta_ads_mcp.core.account_tools.run_preflight_checks',
                side_effect=Exception("Connection failed")
            ):
                result = await validate_credentials()

        data = json.loads(result)
        assert "error" in data
        assert "Connection failed" in data["error"]


class TestGetTokenExpirationStatus:
    """Tests for get_token_expiration_status tool."""

    @pytest.mark.asyncio
    async def test_returns_expiration_info(self, mock_credential_manager):
        """Returns token expiration information."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await get_token_expiration_status()

        data = json.loads(result)
        assert "expiring_soon" in data
        assert "alert_message" in data
        assert "all_keys" in data

    @pytest.mark.asyncio
    async def test_includes_expiring_tokens(self, mock_credential_manager):
        """Includes tokens expiring within threshold."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await get_token_expiration_status()

        data = json.loads(result)
        assert len(data["expiring_soon"]) == 1
        assert data["expiring_soon"][0]["key_name"] == "key2"

    @pytest.mark.asyncio
    async def test_includes_all_keys(self, mock_credential_manager):
        """Includes all keys with their expiration info."""
        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            result = await get_token_expiration_status()

        data = json.loads(result)
        assert len(data["all_keys"]) == 2


class TestToolsReturnValidJson:
    """Tests ensuring all tools return valid JSON."""

    @pytest.mark.asyncio
    async def test_all_tools_return_json(self, mock_credential_manager):
        """All tools return parseable JSON."""
        tools = [
            list_configured_accounts,
            lambda: switch_account("account1"),
            get_current_account,
            get_rate_limit_status,
            get_token_expiration_status,
        ]

        mock_rate_limiter = MagicMock(spec=RateLimiter)
        mock_rate_limiter.get_all_status.return_value = {}
        mock_credential_manager.set_current_account.return_value = True

        with patch(
            'meta_ads_mcp.core.account_tools.get_credential_manager',
            return_value=mock_credential_manager
        ):
            with patch(
                'meta_ads_mcp.core.account_tools.get_rate_limiter',
                return_value=mock_rate_limiter
            ):
                for tool in tools:
                    result = await tool()
                    try:
                        json.loads(result)
                    except json.JSONDecodeError:
                        pytest.fail(f"Tool {tool.__name__} did not return valid JSON")
