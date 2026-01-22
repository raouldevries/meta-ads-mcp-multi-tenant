"""
Tests for preflight validation checks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from meta_ads_mcp.core.preflight import (
    PreflightStatus,
    KeyValidationResult,
    AccountValidationResult,
    PreflightResult,
    validate_token,
    validate_account,
    run_preflight_checks,
    format_preflight_result,
)


class TestPreflightStatus:
    """Tests for PreflightStatus enum."""

    def test_status_values(self):
        """All expected statuses exist."""
        assert PreflightStatus.PASSED.value == "passed"
        assert PreflightStatus.FAILED.value == "failed"
        assert PreflightStatus.WARNING.value == "warning"


class TestKeyValidationResult:
    """Tests for KeyValidationResult dataclass."""

    def test_passed_result(self):
        """Passed result has correct attributes."""
        result = KeyValidationResult(
            key_name="test_key",
            status=PreflightStatus.PASSED,
            user_id="12345",
            user_name="Test User",
            permissions=["ads_read", "ads_management"]
        )
        assert result.key_name == "test_key"
        assert result.status == PreflightStatus.PASSED
        assert result.error is None

    def test_failed_result(self):
        """Failed result has error message."""
        result = KeyValidationResult(
            key_name="bad_key",
            status=PreflightStatus.FAILED,
            error="Invalid token"
        )
        assert result.status == PreflightStatus.FAILED
        assert result.error == "Invalid token"


class TestAccountValidationResult:
    """Tests for AccountValidationResult dataclass."""

    def test_passed_result(self):
        """Passed result has account details."""
        result = AccountValidationResult(
            account_name="my_account",
            status=PreflightStatus.PASSED,
            account_id="act_123456",
            account_status="ACTIVE",
            business_name="Test Business"
        )
        assert result.account_name == "my_account"
        assert result.account_status == "ACTIVE"

    def test_warning_result(self):
        """Warning result for non-active account."""
        result = AccountValidationResult(
            account_name="disabled_account",
            status=PreflightStatus.WARNING,
            account_status="DISABLED",
            error="Account status is DISABLED, not ACTIVE"
        )
        assert result.status == PreflightStatus.WARNING


class TestPreflightResult:
    """Tests for PreflightResult dataclass."""

    def test_passed_property_true(self):
        """passed property returns True for PASSED status."""
        result = PreflightResult(status=PreflightStatus.PASSED)
        assert result.passed is True

    def test_passed_property_false(self):
        """passed property returns False for non-PASSED status."""
        result = PreflightResult(status=PreflightStatus.FAILED)
        assert result.passed is False

    def test_empty_lists_by_default(self):
        """Lists are empty by default."""
        result = PreflightResult(status=PreflightStatus.PASSED)
        assert result.keys == []
        assert result.accounts == []
        assert result.warnings == []
        assert result.errors == []


class TestValidateToken:
    """Tests for validate_token function."""

    @pytest.mark.asyncio
    async def test_valid_token(self):
        """Valid token returns PASSED."""
        # Create mock responses
        me_response = MagicMock()
        me_response.status = 200
        me_response.json = AsyncMock(return_value={
            "id": "12345",
            "name": "Test User"
        })

        perm_response = MagicMock()
        perm_response.status = 200
        perm_response.json = AsyncMock(return_value={
            "data": [
                {"permission": "ads_read", "status": "granted"},
                {"permission": "ads_management", "status": "granted"}
            ]
        })

        # Create async context managers
        me_cm = AsyncMock()
        me_cm.__aenter__.return_value = me_response
        me_cm.__aexit__.return_value = None

        perm_cm = AsyncMock()
        perm_cm.__aenter__.return_value = perm_response
        perm_cm.__aexit__.return_value = None

        # Create session that returns context managers
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[me_cm, perm_cm])

        result = await validate_token(mock_session, "test_key", "valid_token")

        assert result.status == PreflightStatus.PASSED
        assert result.user_id == "12345"
        assert result.user_name == "Test User"
        assert "ads_read" in result.permissions

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Invalid token returns FAILED."""
        error_response = MagicMock()
        error_response.status = 400
        error_response.json = AsyncMock(return_value={
            "error": {"message": "Invalid OAuth access token"}
        })

        error_cm = AsyncMock()
        error_cm.__aenter__.return_value = error_response
        error_cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=error_cm)

        result = await validate_token(mock_session, "bad_key", "invalid_token")

        assert result.status == PreflightStatus.FAILED
        assert "Invalid" in result.error

    @pytest.mark.asyncio
    async def test_missing_permissions(self):
        """Missing required permissions returns WARNING."""
        me_response = MagicMock()
        me_response.status = 200
        me_response.json = AsyncMock(return_value={
            "id": "12345",
            "name": "Test User"
        })

        perm_response = MagicMock()
        perm_response.status = 200
        perm_response.json = AsyncMock(return_value={
            "data": [
                {"permission": "email", "status": "granted"}
            ]
        })

        me_cm = AsyncMock()
        me_cm.__aenter__.return_value = me_response
        me_cm.__aexit__.return_value = None

        perm_cm = AsyncMock()
        perm_cm.__aenter__.return_value = perm_response
        perm_cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[me_cm, perm_cm])

        result = await validate_token(mock_session, "test_key", "limited_token")

        assert result.status == PreflightStatus.WARNING
        assert "Missing permissions" in result.error

    @pytest.mark.asyncio
    async def test_network_error(self):
        """Network error returns FAILED."""
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("Connection refused"))

        result = await validate_token(mock_session, "test_key", "token")

        assert result.status == PreflightStatus.FAILED
        assert "Connection refused" in result.error


class TestValidateAccount:
    """Tests for validate_account function."""

    @pytest.mark.asyncio
    async def test_active_account(self):
        """Active account returns PASSED."""
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "id": "act_123456",
            "name": "Test Account",
            "account_status": 1,  # ACTIVE
            "business": {"name": "Test Business"}
        })

        cm = AsyncMock()
        cm.__aenter__.return_value = response
        cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=cm)

        result = await validate_account(
            mock_session, "test_account", "act_123456", "token"
        )

        assert result.status == PreflightStatus.PASSED
        assert result.account_status == "ACTIVE"
        assert result.business_name == "Test Business"

    @pytest.mark.asyncio
    async def test_disabled_account(self):
        """Disabled account returns WARNING."""
        response = MagicMock()
        response.status = 200
        response.json = AsyncMock(return_value={
            "id": "act_123456",
            "name": "Disabled Account",
            "account_status": 2,  # DISABLED
            "business": {}
        })

        cm = AsyncMock()
        cm.__aenter__.return_value = response
        cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=cm)

        result = await validate_account(
            mock_session, "disabled", "act_123456", "token"
        )

        assert result.status == PreflightStatus.WARNING
        assert result.account_status == "DISABLED"
        assert "not ACTIVE" in result.error

    @pytest.mark.asyncio
    async def test_inaccessible_account(self):
        """Inaccessible account returns FAILED."""
        response = MagicMock()
        response.status = 400
        response.json = AsyncMock(return_value={
            "error": {"message": "No permission to access account"}
        })

        cm = AsyncMock()
        cm.__aenter__.return_value = response
        cm.__aexit__.return_value = None

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=cm)

        result = await validate_account(
            mock_session, "no_access", "act_999999", "token"
        )

        assert result.status == PreflightStatus.FAILED
        assert "permission" in result.error.lower()

    @pytest.mark.asyncio
    async def test_account_status_mapping(self):
        """Account status codes are correctly mapped."""
        status_codes = {
            1: "ACTIVE",
            2: "DISABLED",
            3: "UNSETTLED",
            7: "PENDING_RISK_REVIEW",
            8: "PENDING_SETTLEMENT",
            9: "IN_GRACE_PERIOD",
            100: "PENDING_CLOSURE",
            101: "CLOSED",
        }

        for code, expected_status in status_codes.items():
            response = MagicMock()
            response.status = 200
            response.json = AsyncMock(return_value={
                "id": "act_123",
                "account_status": code,
                "business": {}
            })

            cm = AsyncMock()
            cm.__aenter__.return_value = response
            cm.__aexit__.return_value = None

            mock_session = MagicMock()
            mock_session.get = MagicMock(return_value=cm)

            result = await validate_account(
                mock_session, "test", "act_123", "token"
            )

            assert result.account_status == expected_status, \
                f"Code {code} should map to {expected_status}"


class TestRunPreflightChecks:
    """Tests for run_preflight_checks function."""

    @pytest.fixture
    def mock_credential_manager(self):
        """Create mock CredentialManager."""
        manager = MagicMock()
        manager.api_keys = {}
        manager.accounts = {}
        return manager

    @pytest.mark.asyncio
    async def test_no_aiohttp_returns_warning(self, mock_credential_manager):
        """Returns warning when aiohttp not available."""
        with patch('meta_ads_mcp.core.preflight.AIOHTTP_AVAILABLE', False):
            result = await run_preflight_checks(mock_credential_manager)

        assert result.status == PreflightStatus.WARNING
        assert "aiohttp" in result.warnings[0].lower()

    @pytest.mark.asyncio
    async def test_empty_credentials(self, mock_credential_manager):
        """Empty credentials pass (nothing to validate)."""
        # Since aiohttp is conditionally imported, we need to mock it properly
        import aiohttp

        mock_session = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_session
        mock_cm.__aexit__.return_value = None

        with patch.object(aiohttp, 'ClientSession', return_value=mock_cm):
            result = await run_preflight_checks(mock_credential_manager)

        assert result.status == PreflightStatus.PASSED

    @pytest.mark.asyncio
    async def test_failed_key_skips_accounts(self, mock_credential_manager):
        """Accounts with failed keys are skipped."""
        import aiohttp

        # Set up mock credential manager with a key and account
        mock_key = MagicMock()
        mock_key.name = "bad_key"
        mock_key.access_token = "invalid_token"
        mock_credential_manager.api_keys = {"bad_key": mock_key}

        mock_account = MagicMock()
        mock_account.name = "test_account"
        mock_account.api_key = "bad_key"
        mock_account.ad_account_id = "act_123"
        mock_credential_manager.accounts = {"test_account": mock_account}

        mock_session = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_session
        mock_cm.__aexit__.return_value = None

        with patch('meta_ads_mcp.core.preflight.validate_token') as mock_validate:
            mock_validate.return_value = KeyValidationResult(
                key_name="bad_key",
                status=PreflightStatus.FAILED,
                error="Invalid token"
            )

            with patch.object(aiohttp, 'ClientSession', return_value=mock_cm):
                result = await run_preflight_checks(mock_credential_manager)

        # Account should be marked as failed due to key failure
        assert any(
            acc.account_name == "test_account" and
            "bad_key" in acc.error and
            acc.status == PreflightStatus.FAILED
            for acc in result.accounts
        )


class TestFormatPreflightResult:
    """Tests for format_preflight_result function."""

    def test_format_passed(self):
        """Format passed result."""
        result = PreflightResult(
            status=PreflightStatus.PASSED,
            keys=[KeyValidationResult(
                key_name="key1",
                status=PreflightStatus.PASSED,
                user_id="123",
                user_name="Test User"
            )],
            accounts=[AccountValidationResult(
                account_name="acc1",
                status=PreflightStatus.PASSED,
                account_id="act_123",
                account_status="ACTIVE"
            )]
        )

        output = format_preflight_result(result)

        assert "[PASSED]" in output
        assert "key1" in output
        assert "Test User" in output
        assert "acc1" in output
        assert "ACTIVE" in output

    def test_format_failed(self):
        """Format failed result."""
        result = PreflightResult(
            status=PreflightStatus.FAILED,
            keys=[KeyValidationResult(
                key_name="bad_key",
                status=PreflightStatus.FAILED,
                error="Invalid token"
            )],
            errors=["Key 'bad_key': Invalid token"]
        )

        output = format_preflight_result(result)

        assert "[FAILED]" in output
        assert "bad_key" in output
        assert "Invalid token" in output
        assert "[ERROR]" in output

    def test_format_warning(self):
        """Format warning result."""
        result = PreflightResult(
            status=PreflightStatus.WARNING,
            warnings=["Token expires in 3 days"]
        )

        output = format_preflight_result(result)

        assert "[WARNING]" in output
        assert "[WARN]" in output
        assert "expires" in output

    def test_format_empty(self):
        """Format empty result."""
        result = PreflightResult(status=PreflightStatus.PASSED)
        output = format_preflight_result(result)

        assert "[PASSED]" in output
        assert "PASSED" in output
