"""
Tests for Meta Graph API error classification.
"""

import pytest

from meta_ads_mcp.core.errors import (
    ErrorAction,
    ErrorClassification,
    classify_error,
    MetaApiError,
    ERROR_MAP,
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


class TestErrorClassification:
    """Tests for ErrorClassification dataclass."""

    def test_classification_attributes(self):
        """Classification has all required attributes."""
        classification = ErrorClassification(
            code=100,
            subcode=None,
            action=ErrorAction.BAD_REQUEST,
            retryable=False,
            max_retries=0,
            description="Test error"
        )
        assert classification.code == 100
        assert classification.action == ErrorAction.BAD_REQUEST
        assert classification.retryable is False


class TestErrorMap:
    """Tests for error code mapping."""

    def test_oauth_error_190(self):
        """Error 190 is classified as auth error."""
        classification = ERROR_MAP[190]
        assert classification.action == ErrorAction.AUTH_ERROR
        assert classification.retryable is False
        assert classification.max_retries == 0

    def test_rate_limit_error_4(self):
        """Error 4 is classified as rate limit."""
        classification = ERROR_MAP[4]
        assert classification.action == ErrorAction.RATE_LIMIT
        assert classification.retryable is True
        assert classification.max_retries == 3

    def test_rate_limit_error_17(self):
        """Error 17 is classified as rate limit."""
        classification = ERROR_MAP[17]
        assert classification.action == ErrorAction.RATE_LIMIT
        assert classification.retryable is True

    def test_rate_limit_error_32(self):
        """Error 32 is classified as rate limit."""
        classification = ERROR_MAP[32]
        assert classification.action == ErrorAction.RATE_LIMIT

    def test_rate_limit_error_613(self):
        """Error 613 is classified as rate limit."""
        classification = ERROR_MAP[613]
        assert classification.action == ErrorAction.RATE_LIMIT

    def test_permission_error_10(self):
        """Error 10 is classified as permission error."""
        classification = ERROR_MAP[10]
        assert classification.action == ErrorAction.PERM_ERROR
        assert classification.retryable is False

    def test_permission_error_200(self):
        """Error 200 is classified as permission error."""
        classification = ERROR_MAP[200]
        assert classification.action == ErrorAction.PERM_ERROR

    def test_permission_error_294(self):
        """Error 294 is classified as permission error."""
        classification = ERROR_MAP[294]
        assert classification.action == ErrorAction.PERM_ERROR

    def test_bad_request_error_100(self):
        """Error 100 is classified as bad request."""
        classification = ERROR_MAP[100]
        assert classification.action == ErrorAction.BAD_REQUEST
        assert classification.retryable is False

    def test_server_error_1(self):
        """Error 1 is classified as server error."""
        classification = ERROR_MAP[1]
        assert classification.action == ErrorAction.SERVER_ERROR
        assert classification.retryable is True
        assert classification.max_retries == 3

    def test_server_error_2(self):
        """Error 2 is classified as server error."""
        classification = ERROR_MAP[2]
        assert classification.action == ErrorAction.SERVER_ERROR
        assert classification.retryable is True


class TestClassifyError:
    """Tests for classify_error function."""

    def test_classify_known_error(self):
        """Known error code returns correct classification."""
        classification = classify_error(190)
        assert classification.code == 190
        assert classification.action == ErrorAction.AUTH_ERROR

    def test_classify_unknown_error(self):
        """Unknown error code returns UNKNOWN classification."""
        classification = classify_error(99999)
        assert classification.code == 99999
        assert classification.action == ErrorAction.UNKNOWN
        assert classification.retryable is False

    def test_classify_with_subcode(self):
        """Subcode is preserved in classification."""
        classification = classify_error(100, error_subcode=123)
        # Currently subcodes aren't used for lookup, but should be preserved
        # for future enhancements
        assert classification.code == 100


class TestMetaApiError:
    """Tests for MetaApiError exception."""

    def test_error_creation(self):
        """Error is created with correct attributes."""
        error = MetaApiError(
            message="Test error message",
            error_code=4,
            error_subcode=123,
            retry_after=60
        )
        assert error.message == "Test error message"
        assert error.error_code == 4
        assert error.error_subcode == 123
        assert error.retry_after == 60

    def test_error_classification(self):
        """Error has correct classification."""
        error = MetaApiError(
            message="Rate limit",
            error_code=4
        )
        assert error.classification.action == ErrorAction.RATE_LIMIT

    def test_is_retryable_true(self):
        """Retryable errors return True."""
        error = MetaApiError(
            message="Rate limit",
            error_code=4
        )
        assert error.is_retryable is True

    def test_is_retryable_false(self):
        """Non-retryable errors return False."""
        error = MetaApiError(
            message="Invalid token",
            error_code=190
        )
        assert error.is_retryable is False

    def test_action_property(self):
        """Action property returns correct action."""
        error = MetaApiError(
            message="Permission denied",
            error_code=200
        )
        assert error.action == ErrorAction.PERM_ERROR

    def test_max_retries_property(self):
        """Max retries property returns correct value."""
        error = MetaApiError(
            message="Server error",
            error_code=2
        )
        assert error.max_retries == 3

    def test_to_dict(self):
        """to_dict returns correct dictionary."""
        error = MetaApiError(
            message="Test error",
            error_code=4,
            error_subcode=100,
            retry_after=30
        )
        result = error.to_dict()

        assert result["error"] == "Test error"
        assert result["error_code"] == 4
        assert result["error_subcode"] == 100
        assert result["action"] == "rate_limit"
        assert result["retryable"] is True
        assert result["retry_after"] == 30

    def test_exception_str(self):
        """Exception string representation."""
        error = MetaApiError(
            message="Test error message",
            error_code=100
        )
        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """MetaApiError inherits from Exception."""
        error = MetaApiError(
            message="Test",
            error_code=100
        )
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Error can be raised and caught."""
        with pytest.raises(MetaApiError) as exc_info:
            raise MetaApiError(
                message="Test error",
                error_code=190
            )

        assert exc_info.value.error_code == 190


class TestErrorClassificationDetails:
    """Tests for specific error classification details."""

    def test_all_rate_limit_errors_are_retryable(self):
        """All rate limit errors should be retryable."""
        rate_limit_codes = [4, 17, 32, 613]
        for code in rate_limit_codes:
            classification = classify_error(code)
            assert classification.retryable is True, f"Error {code} should be retryable"
            assert classification.action == ErrorAction.RATE_LIMIT

    def test_all_auth_errors_are_not_retryable(self):
        """Auth errors should not be retryable."""
        classification = classify_error(190)
        assert classification.retryable is False
        assert classification.max_retries == 0

    def test_server_errors_have_retries(self):
        """Server errors should have retry attempts."""
        server_codes = [1, 2]
        for code in server_codes:
            classification = classify_error(code)
            assert classification.max_retries > 0

    def test_permission_errors_not_retryable(self):
        """Permission errors should not be retryable."""
        perm_codes = [10, 200, 294]
        for code in perm_codes:
            classification = classify_error(code)
            assert classification.retryable is False
            assert classification.max_retries == 0
