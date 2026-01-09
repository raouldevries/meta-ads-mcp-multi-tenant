"""Tests for token validation tools (get_token_info, validate_token)."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from meta_ads_mcp.core.accounts import get_token_info, validate_token


class TestGetTokenInfo:
    """Tests for get_token_info tool."""

    @pytest.mark.asyncio
    async def test_get_token_info_no_token(self):
        """Test get_token_info returns error when no token is configured."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await get_token_info()
            data = json.loads(result)

            assert "error" in data
            assert "No access token configured" in data["error"]
            assert "help" in data

    @pytest.mark.asyncio
    async def test_get_token_info_valid_token(self):
        """Test get_token_info returns detailed token information."""
        mock_response = {
            "data": {
                "is_valid": True,
                "app_id": "123456789",
                "type": "USER",
                "user_id": "987654321",
                "expires_at": 0,
                "scopes": ["ads_management", "ads_read", "business_management"],
                "granular_scopes": [],
                "issued_at": 1704067200
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await get_token_info()
                data = json.loads(result)

                assert data["is_valid"] is True
                assert data["type"] == "USER"
                assert data["app_id"] == "123456789"
                assert data["user_id"] == "987654321"
                assert "ads_management" in data["scopes"]
                assert "token_prefix" in data
                assert data["expiration"] == "Never (long-lived token)"

    @pytest.mark.asyncio
    async def test_get_token_info_with_expiration(self):
        """Test get_token_info handles tokens with expiration."""
        import time
        future_expiry = int(time.time()) + 86400 * 30  # 30 days from now

        mock_response = {
            "data": {
                "is_valid": True,
                "app_id": "123456789",
                "type": "USER",
                "expires_at": future_expiry,
                "scopes": ["ads_read"]
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await get_token_info()
                data = json.loads(result)

                assert isinstance(data["expiration"], dict)
                assert "remaining_days" in data["expiration"]
                assert data["expiration"]["remaining_days"] >= 29

    @pytest.mark.asyncio
    async def test_get_token_info_api_error(self):
        """Test get_token_info handles API errors."""
        mock_response = {
            "error": {
                "message": "Invalid OAuth access token",
                "code": 190
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "invalid_token_here"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await get_token_info()
                data = json.loads(result)

                assert "error" in data
                assert data["error_code"] == 190

    @pytest.mark.asyncio
    async def test_get_token_info_with_explicit_token(self):
        """Test get_token_info uses explicitly provided token."""
        mock_response = {
            "data": {
                "is_valid": True,
                "app_id": "explicit_app",
                "type": "USER"
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "should_not_use"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await get_token_info(access_token="explicit_token_here")
                data = json.loads(result)

                assert "explicit_token" in data["token_prefix"]

    @pytest.mark.asyncio
    async def test_get_token_info_network_error(self):
        """Test get_token_info handles network errors gracefully."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get.side_effect = Exception("Connection refused")

                result = await get_token_info()
                data = json.loads(result)

                assert "error" in data
                assert "Connection refused" in data["error"]


class TestValidateToken:
    """Tests for validate_token tool."""

    @pytest.mark.asyncio
    async def test_validate_token_no_token(self):
        """Test validate_token returns error when no token is configured."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await validate_token()
            data = json.loads(result)

            assert data["valid"] is False
            assert "No token configured" in data["message"]
            assert "action" in data

    @pytest.mark.asyncio
    async def test_validate_token_valid(self):
        """Test validate_token returns success for valid token."""
        mock_response = {
            "id": "123456789"
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "valid_token_here"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is True
                assert data["user_id"] == "123456789"
                assert "working" in data["message"]

    @pytest.mark.asyncio
    async def test_validate_token_expired(self):
        """Test validate_token handles expired token."""
        mock_response = {
            "error": {
                "message": "Error validating access token",
                "code": 190
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "expired_token"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is False
                assert data["error_code"] == 190
                assert "Generate new token" in data["action"]

    @pytest.mark.asyncio
    async def test_validate_token_rate_limited(self):
        """Test validate_token handles rate limit errors."""
        mock_response = {
            "error": {
                "message": "Application request limit reached",
                "code": 4
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is False
                assert data["error_code"] == 4
                assert "Wait and retry" in data["action"]

    @pytest.mark.asyncio
    async def test_validate_token_session_expired(self):
        """Test validate_token handles session expired error."""
        mock_response = {
            "error": {
                "message": "Session has expired",
                "code": 102
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is False
                assert data["error_code"] == 102
                assert "Re-authenticate" in data["action"]

    @pytest.mark.asyncio
    async def test_validate_token_network_error(self):
        """Test validate_token handles network errors."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get.side_effect = Exception("Network timeout")

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is False
                assert "Network timeout" in data["message"]
                assert "Check network connectivity" in data["action"]

    @pytest.mark.asyncio
    async def test_validate_token_unknown_error(self):
        """Test validate_token handles unknown error codes."""
        mock_response = {
            "error": {
                "message": "Unknown error",
                "code": 999
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token()
                data = json.loads(result)

                assert data["valid"] is False
                assert "Check token and permissions" in data["action"]

    @pytest.mark.asyncio
    async def test_validate_token_with_explicit_token(self):
        """Test validate_token uses explicitly provided token."""
        mock_response = {"id": "explicit_user_id"}

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "should_not_use"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_http_response = MagicMock()
                mock_http_response.json.return_value = mock_response
                mock_client.get.return_value = mock_http_response

                result = await validate_token(access_token="explicit_token")
                data = json.loads(result)

                assert data["valid"] is True
                assert data["user_id"] == "explicit_user_id"


class TestTokenValidationResponseFormat:
    """Tests for response format validation."""

    @pytest.mark.asyncio
    async def test_get_token_info_is_valid_json(self):
        """Test that get_token_info always returns valid JSON."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await get_token_info()
            data = json.loads(result)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_validate_token_is_valid_json(self):
        """Test that validate_token always returns valid JSON."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await validate_token()
            data = json.loads(result)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_validate_token_has_required_fields(self):
        """Test that validate_token response has required fields."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await validate_token()
            data = json.loads(result)

            assert "valid" in data
            assert "message" in data
            assert isinstance(data["valid"], bool)
