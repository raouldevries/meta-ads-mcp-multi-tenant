"""Tests for the health_check tool."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from meta_ads_mcp.core.accounts import health_check


class TestHealthCheck:
    """Tests for health_check tool."""

    @pytest.mark.asyncio
    async def test_health_check_no_token(self):
        """Test health_check returns error when no token is configured."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await health_check()
            data = json.loads(result)

            assert data["status"] == "error"
            assert data["checks"]["token"]["status"] == "failed"
            assert "No access token configured" in data["checks"]["token"]["message"]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health_check returns healthy status when all checks pass."""
        mock_token_response = {
            "data": {
                "is_valid": True,
                "app_id": "123456789",
                "type": "USER",
                "expires_at": 0,
                "scopes": ["ads_management", "ads_read"]
            }
        }

        mock_accounts_response = {
            "data": [
                {"id": "act_111", "name": "Account 1", "account_status": 1},
                {"id": "act_222", "name": "Account 2", "account_status": 1}
            ]
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                # Mock responses for both API calls
                mock_response_token = MagicMock()
                mock_response_token.json.return_value = mock_token_response

                mock_response_accounts = MagicMock()
                mock_response_accounts.json.return_value = mock_accounts_response

                mock_client.get.side_effect = [mock_response_token, mock_response_accounts]

                result = await health_check()
                data = json.loads(result)

                assert data["status"] == "healthy"
                assert data["checks"]["token"]["status"] == "present"
                assert data["checks"]["token_validation"]["status"] == "valid"
                assert data["checks"]["token_validation"]["app_id"] == "123456789"
                assert data["checks"]["ad_accounts"]["status"] == "accessible"
                assert data["checks"]["ad_accounts"]["count"] == 2
                assert "diagnostics" in data
                assert "total_latency_ms" in data["diagnostics"]

    @pytest.mark.asyncio
    async def test_health_check_invalid_token(self):
        """Test health_check returns unhealthy when token is invalid."""
        mock_token_response = {
            "data": {
                "is_valid": False,
                "error": {
                    "message": "Token expired"
                }
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "invalid_token_here"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response = MagicMock()
                mock_response.json.return_value = mock_token_response
                mock_client.get.return_value = mock_response

                result = await health_check()
                data = json.loads(result)

                assert data["status"] == "unhealthy"
                assert data["checks"]["token_validation"]["status"] == "invalid"

    @pytest.mark.asyncio
    async def test_health_check_degraded_status(self):
        """Test health_check returns degraded when token valid but accounts inaccessible."""
        mock_token_response = {
            "data": {
                "is_valid": True,
                "app_id": "123456789",
                "type": "USER"
            }
        }

        mock_accounts_error = {
            "error": {
                "message": "Permission denied"
            }
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response_token = MagicMock()
                mock_response_token.json.return_value = mock_token_response

                mock_response_accounts = MagicMock()
                mock_response_accounts.json.return_value = mock_accounts_error

                mock_client.get.side_effect = [mock_response_token, mock_response_accounts]

                result = await health_check()
                data = json.loads(result)

                assert data["status"] == "degraded"
                assert data["checks"]["token_validation"]["status"] == "valid"
                assert data["checks"]["ad_accounts"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_with_explicit_token(self):
        """Test health_check uses explicitly provided token."""
        mock_token_response = {
            "data": {
                "is_valid": True,
                "app_id": "explicit_app",
                "type": "USER"
            }
        }

        mock_accounts_response = {
            "data": [{"id": "act_123", "name": "Test", "account_status": 1}]
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            # Should not be called when explicit token provided
            mock_auth.return_value = "should_not_use_this"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response_token = MagicMock()
                mock_response_token.json.return_value = mock_token_response

                mock_response_accounts = MagicMock()
                mock_response_accounts.json.return_value = mock_accounts_response

                mock_client.get.side_effect = [mock_response_token, mock_response_accounts]

                result = await health_check(access_token="explicit_token_here")
                data = json.loads(result)

                assert data["status"] == "healthy"
                # Verify explicit token was used (check the prefix in result)
                assert "explicit_token" in data["checks"]["token"]["prefix"]

    @pytest.mark.asyncio
    async def test_health_check_api_error_handling(self):
        """Test health_check handles API errors gracefully."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                # Simulate API error
                mock_client.get.side_effect = Exception("Network error")

                result = await health_check()
                data = json.loads(result)

                # Should handle error gracefully
                assert data["checks"]["token_validation"]["status"] == "error"
                assert "Network error" in data["checks"]["token_validation"]["error"]

    @pytest.mark.asyncio
    async def test_health_check_includes_diagnostics(self):
        """Test health_check includes diagnostic information."""
        mock_token_response = {
            "data": {
                "is_valid": True,
                "app_id": "123",
                "type": "USER"
            }
        }

        mock_accounts_response = {
            "data": [{"id": "act_123", "name": "Test", "account_status": 1}]
        }

        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "test_token_12345678901234567890"

            with patch('meta_ads_mcp.core.accounts.httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client

                mock_response_token = MagicMock()
                mock_response_token.json.return_value = mock_token_response

                mock_response_accounts = MagicMock()
                mock_response_accounts.json.return_value = mock_accounts_response

                mock_client.get.side_effect = [mock_response_token, mock_response_accounts]

                result = await health_check()
                data = json.loads(result)

                assert "diagnostics" in data
                assert "total_latency_ms" in data["diagnostics"]
                assert "api_base" in data["diagnostics"]
                assert "timestamp" in data["diagnostics"]
                assert isinstance(data["diagnostics"]["total_latency_ms"], int)


class TestHealthCheckResponseFormat:
    """Tests for health_check response format validation."""

    @pytest.mark.asyncio
    async def test_response_is_valid_json(self):
        """Test that response is always valid JSON."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await health_check()

            # Should not raise
            data = json.loads(result)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_response_has_required_fields(self):
        """Test that response always has required fields."""
        with patch('meta_ads_mcp.core.accounts.get_current_access_token', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = None

            result = await health_check()
            data = json.loads(result)

            # Required top-level fields
            assert "status" in data
            assert "checks" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy", "error", "unknown"]
