"""
Tests for Meta Graph API error classification in retry module.

Tests ErrorAction enum and action classification integrated into retry.py.
"""

import pytest

from meta_ads_mcp.core.retry import (
    ErrorAction,
    MetaApiError,
    RetryConfig,
)


class TestErrorAction:
    """Tests for ErrorAction enum."""

    def test_all_actions_defined(self):
        """All expected actions are defined."""
        expected = [
            "RETRY", "RATE_LIMIT", "AUTH_ERROR", "PERM_ERROR",
            "NOT_FOUND", "BAD_REQUEST", "SERVER_ERROR", "UNKNOWN"
        ]
        for action in expected:
            assert hasattr(ErrorAction, action)

    def test_action_values(self):
        """Action values are correct strings."""
        assert ErrorAction.RETRY.value == "retry"
        assert ErrorAction.RATE_LIMIT.value == "rate_limit"
        assert ErrorAction.AUTH_ERROR.value == "auth_error"
        assert ErrorAction.PERM_ERROR.value == "perm_error"
        assert ErrorAction.NOT_FOUND.value == "not_found"
        assert ErrorAction.BAD_REQUEST.value == "bad_req"
        assert ErrorAction.SERVER_ERROR.value == "server"
        assert ErrorAction.UNKNOWN.value == "unknown"


class TestRetryConfigErrorActions:
    """Tests for error code to action mapping."""

    def test_oauth_error_190(self):
        """Error 190 is classified as auth error."""
        action = RetryConfig.get_action(error_code=190)
        assert action == ErrorAction.AUTH_ERROR

    def test_rate_limit_error_4(self):
        """Error 4 is classified as rate limit."""
        action = RetryConfig.get_action(error_code=4)
        assert action == ErrorAction.RATE_LIMIT

    def test_rate_limit_error_17(self):
        """Error 17 is classified as rate limit."""
        action = RetryConfig.get_action(error_code=17)
        assert action == ErrorAction.RATE_LIMIT

    def test_rate_limit_error_32(self):
        """Error 32 is classified as rate limit."""
        action = RetryConfig.get_action(error_code=32)
        assert action == ErrorAction.RATE_LIMIT

    def test_rate_limit_error_613(self):
        """Error 613 is classified as rate limit."""
        action = RetryConfig.get_action(error_code=613)
        assert action == ErrorAction.RATE_LIMIT

    def test_rate_limit_error_80000(self):
        """Error 80000 is classified as rate limit."""
        action = RetryConfig.get_action(error_code=80000)
        assert action == ErrorAction.RATE_LIMIT

    def test_permission_error_10(self):
        """Error 10 is classified as permission error."""
        action = RetryConfig.get_action(error_code=10)
        assert action == ErrorAction.PERM_ERROR

    def test_permission_error_200(self):
        """Error 200 is classified as permission error."""
        action = RetryConfig.get_action(error_code=200)
        assert action == ErrorAction.PERM_ERROR

    def test_permission_error_294(self):
        """Error 294 is classified as permission error."""
        action = RetryConfig.get_action(error_code=294)
        assert action == ErrorAction.PERM_ERROR

    def test_bad_request_error_100(self):
        """Error 100 is classified as bad request."""
        action = RetryConfig.get_action(error_code=100)
        assert action == ErrorAction.BAD_REQUEST

    def test_server_error_1(self):
        """Error 1 is classified as server error."""
        action = RetryConfig.get_action(error_code=1)
        assert action == ErrorAction.SERVER_ERROR

    def test_server_error_2(self):
        """Error 2 is classified as server error."""
        action = RetryConfig.get_action(error_code=2)
        assert action == ErrorAction.SERVER_ERROR

    def test_unknown_error_code(self):
        """Unknown error code returns UNKNOWN action."""
        action = RetryConfig.get_action(error_code=99999)
        assert action == ErrorAction.UNKNOWN


class TestRetryConfigHttpStatusActions:
    """Tests for HTTP status code to action mapping."""

    def test_http_401_is_auth_error(self):
        """HTTP 401 is classified as auth error."""
        action = RetryConfig.get_action(status_code=401)
        assert action == ErrorAction.AUTH_ERROR

    def test_http_403_is_auth_error(self):
        """HTTP 403 is classified as auth error."""
        action = RetryConfig.get_action(status_code=403)
        assert action == ErrorAction.AUTH_ERROR

    def test_http_404_is_not_found(self):
        """HTTP 404 is classified as not found."""
        action = RetryConfig.get_action(status_code=404)
        assert action == ErrorAction.NOT_FOUND

    def test_http_429_is_rate_limit(self):
        """HTTP 429 is classified as rate limit."""
        action = RetryConfig.get_action(status_code=429)
        assert action == ErrorAction.RATE_LIMIT

    def test_http_500_is_server_error(self):
        """HTTP 500 is classified as server error."""
        action = RetryConfig.get_action(status_code=500)
        assert action == ErrorAction.SERVER_ERROR

    def test_http_502_is_server_error(self):
        """HTTP 502 is classified as server error."""
        action = RetryConfig.get_action(status_code=502)
        assert action == ErrorAction.SERVER_ERROR

    def test_http_503_is_server_error(self):
        """HTTP 503 is classified as server error."""
        action = RetryConfig.get_action(status_code=503)
        assert action == ErrorAction.SERVER_ERROR

    def test_http_400_is_bad_request(self):
        """HTTP 400 is classified as bad request."""
        action = RetryConfig.get_action(status_code=400)
        assert action == ErrorAction.BAD_REQUEST


class TestMetaApiErrorAction:
    """Tests for MetaApiError action property."""

    def test_error_action_rate_limit(self):
        """Error with rate limit code has RATE_LIMIT action."""
        error = MetaApiError(
            message="Rate limit",
            error_code=4
        )
        assert error.action == ErrorAction.RATE_LIMIT

    def test_error_action_auth_error(self):
        """Error with auth code has AUTH_ERROR action."""
        error = MetaApiError(
            message="Invalid token",
            error_code=190
        )
        assert error.action == ErrorAction.AUTH_ERROR

    def test_error_action_perm_error(self):
        """Error with permission code has PERM_ERROR action."""
        error = MetaApiError(
            message="Permission denied",
            error_code=200
        )
        assert error.action == ErrorAction.PERM_ERROR

    def test_error_action_bad_request(self):
        """Error with bad request code has BAD_REQUEST action."""
        error = MetaApiError(
            message="Invalid parameter",
            error_code=100
        )
        assert error.action == ErrorAction.BAD_REQUEST

    def test_error_action_server_error(self):
        """Error with server error code has SERVER_ERROR action."""
        error = MetaApiError(
            message="Server error",
            error_code=2
        )
        assert error.action == ErrorAction.SERVER_ERROR

    def test_error_action_from_http_status(self):
        """Error with HTTP status uses status for action."""
        error = MetaApiError(
            message="Not found",
            status_code=404
        )
        assert error.action == ErrorAction.NOT_FOUND

    def test_error_action_unknown(self):
        """Error with unknown code has UNKNOWN action."""
        error = MetaApiError(
            message="Unknown error",
            error_code=99999
        )
        assert error.action == ErrorAction.UNKNOWN


class TestMetaApiErrorToDictWithAction:
    """Tests for to_dict including action."""

    def test_to_dict_includes_action(self):
        """to_dict includes action field."""
        error = MetaApiError(
            message="Test error",
            error_code=4,
            error_subcode=100,
            retry_after=30
        )
        result = error.to_dict()

        assert result["message"] == "Test error"
        assert result["error_code"] == 4
        assert result["error_subcode"] == 100
        assert result["action"] == "rate_limit"
        assert result["is_retryable"] is True

    def test_to_dict_auth_error_action(self):
        """to_dict shows auth_error action."""
        error = MetaApiError(
            message="Invalid token",
            error_code=190
        )
        result = error.to_dict()
        assert result["action"] == "auth_error"
        assert result["is_retryable"] is False


class TestErrorActionConsistency:
    """Tests for consistency between action and retryable."""

    def test_rate_limit_errors_are_retryable(self):
        """All rate limit errors should be retryable."""
        rate_limit_codes = [4, 17, 32, 613, 80000, 80001, 80002]
        for code in rate_limit_codes:
            error = MetaApiError(message="Rate limit", error_code=code)
            assert error.action == ErrorAction.RATE_LIMIT
            assert error.is_retryable is True, f"Error {code} should be retryable"

    def test_auth_errors_are_not_retryable(self):
        """Auth errors should not be retryable."""
        error = MetaApiError(message="Invalid token", error_code=190)
        assert error.action == ErrorAction.AUTH_ERROR
        assert error.is_retryable is False

    def test_server_errors_are_retryable(self):
        """Server errors should be retryable."""
        server_codes = [1, 2]
        for code in server_codes:
            error = MetaApiError(message="Server error", error_code=code)
            assert error.action == ErrorAction.SERVER_ERROR
            assert error.is_retryable is True

    def test_permission_errors_not_retryable(self):
        """Permission errors should not be retryable."""
        perm_codes = [10, 200, 294]
        for code in perm_codes:
            error = MetaApiError(message="Permission denied", error_code=code)
            assert error.action == ErrorAction.PERM_ERROR
            assert error.is_retryable is False
