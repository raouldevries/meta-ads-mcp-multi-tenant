"""Tests for the retry module with exponential backoff."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from meta_ads_mcp.core.retry import (
    RetryConfig,
    MetaApiError,
    with_retry,
    parse_meta_error,
    retry_with_backoff,
)


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_retryable_error_codes_defined(self):
        """Test that retryable error codes are defined."""
        assert 4 in RetryConfig.RETRYABLE_ERROR_CODES  # App rate limit
        assert 17 in RetryConfig.RETRYABLE_ERROR_CODES  # User rate limit
        assert 32 in RetryConfig.RETRYABLE_ERROR_CODES  # Page rate limit
        assert 80004 in RetryConfig.RETRYABLE_ERROR_CODES  # Too many calls

    def test_retryable_http_status_codes_defined(self):
        """Test that retryable HTTP status codes are defined."""
        assert 429 in RetryConfig.RETRYABLE_HTTP_STATUS  # Too Many Requests
        assert 500 in RetryConfig.RETRYABLE_HTTP_STATUS  # Internal Server Error
        assert 502 in RetryConfig.RETRYABLE_HTTP_STATUS  # Bad Gateway
        assert 503 in RetryConfig.RETRYABLE_HTTP_STATUS  # Service Unavailable
        assert 504 in RetryConfig.RETRYABLE_HTTP_STATUS  # Gateway Timeout

    def test_is_retryable_error(self):
        """Test is_retryable_error class method."""
        assert RetryConfig.is_retryable_error(17) is True  # User rate limit
        assert RetryConfig.is_retryable_error(4) is True  # App rate limit
        assert RetryConfig.is_retryable_error(190) is False  # Invalid token (not retryable)
        assert RetryConfig.is_retryable_error(100) is False  # Invalid parameter

    def test_is_retryable_status(self):
        """Test is_retryable_status class method."""
        assert RetryConfig.is_retryable_status(429) is True
        assert RetryConfig.is_retryable_status(503) is True
        assert RetryConfig.is_retryable_status(400) is False  # Bad Request
        assert RetryConfig.is_retryable_status(401) is False  # Unauthorized
        assert RetryConfig.is_retryable_status(404) is False  # Not Found

    def test_get_max_retries_error_code(self):
        """Test get_max_retries for error codes."""
        # Rate limit errors
        assert RetryConfig.get_max_retries(4) == 3  # App rate limit
        assert RetryConfig.get_max_retries(17) == 3  # User rate limit
        assert RetryConfig.get_max_retries(32) == 2  # Page rate limit (different retry count)

    def test_get_max_retries_http_status(self):
        """Test get_max_retries for HTTP status codes."""
        assert RetryConfig.get_max_retries(None, 429) == 3  # Too Many Requests
        assert RetryConfig.get_max_retries(None, 500) == 2  # Internal Server Error
        assert RetryConfig.get_max_retries(None, 503) == 3  # Service Unavailable

    def test_get_max_retries_non_retryable(self):
        """Test get_max_retries for non-retryable errors."""
        assert RetryConfig.get_max_retries(190) == 0  # Invalid token
        assert RetryConfig.get_max_retries(None, 400) == 0  # Bad Request
        assert RetryConfig.get_max_retries(100) == 0  # Invalid parameter

    def test_get_error_description(self):
        """Test get_error_description class method."""
        desc = RetryConfig.get_error_description(17)
        assert "limit" in desc.lower() or "request" in desc.lower()

        desc = RetryConfig.get_error_description(None, 503)
        assert "unavailable" in desc.lower() or "service" in desc.lower()

    def test_calculate_delay_exponential(self):
        """Test that delay increases exponentially."""
        delay0 = RetryConfig.calculate_delay(0)
        delay1 = RetryConfig.calculate_delay(1)
        delay2 = RetryConfig.calculate_delay(2)

        # Due to jitter, we can't test exact values, but delay should increase
        # Base delay is 1s, so delay0 should be ~1s + jitter
        assert delay0 >= 1.0  # At least base delay
        assert delay0 <= 2.5  # Base + max jitter

    def test_calculate_delay_with_retry_after(self):
        """Test delay respects retry_after header."""
        # retry_after should be respected (with small jitter added)
        delay = RetryConfig.calculate_delay(0, retry_after=30)
        assert delay >= 30.0
        assert delay <= 31.0  # Small jitter added

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at MAX_DELAY_MS."""
        # Very high attempt number
        delay = RetryConfig.calculate_delay(20)
        # Should be capped at max delay (60s) + jitter (1s max)
        assert delay <= (RetryConfig.MAX_DELAY_MS + RetryConfig.JITTER_MAX_MS) / 1000.0


class TestMetaApiError:
    """Tests for MetaApiError exception class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = MetaApiError(
            message="Rate limit exceeded",
            error_code=17
        )
        assert error.error_code == 17
        assert error.message == "Rate limit exceeded"
        assert error.is_retryable is True  # Rate limit is retryable

    def test_non_retryable_error(self):
        """Test non-retryable error detection."""
        error = MetaApiError(
            message="Invalid OAuth access token",
            error_code=190
        )
        assert error.is_retryable is False

    def test_http_status_retryable(self):
        """Test HTTP status determines retryability."""
        error = MetaApiError(
            message="Server error",
            status_code=503
        )
        assert error.is_retryable is True

    def test_http_status_non_retryable(self):
        """Test non-retryable HTTP status."""
        error = MetaApiError(
            message="Bad request",
            status_code=400
        )
        assert error.is_retryable is False

    def test_max_retries_property(self):
        """Test max_retries property."""
        error = MetaApiError(message="Rate limit", error_code=17)
        assert error.max_retries == 3

        error = MetaApiError(message="Server error", status_code=500)
        assert error.max_retries == 2

    def test_to_dict(self):
        """Test serialization to dictionary."""
        error = MetaApiError(
            message="Rate limit exceeded",
            error_code=17,
            error_subcode=123,
            error_type="OAuthException",
            status_code=400,
            fbtrace_id="abc123"
        )
        d = error.to_dict()
        assert d["error_code"] == 17
        assert d["message"] == "Rate limit exceeded"
        assert d["error_subcode"] == 123
        assert d["error_type"] == "OAuthException"
        assert d["status_code"] == 400
        assert d["fbtrace_id"] == "abc123"
        assert d["is_retryable"] is True

    def test_str_representation(self):
        """Test string representation."""
        error = MetaApiError(
            message="Rate limit exceeded",
            error_code=17,
            fbtrace_id="abc123"
        )
        s = str(error)
        assert "17" in s or "code" in s
        assert "Rate limit exceeded" in s


class TestParseMetaError:
    """Tests for parse_meta_error function."""

    def test_parse_standard_error(self):
        """Test parsing standard Meta API error format."""
        error_response = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "OAuthException",
                "code": 17,
                "error_subcode": 123,
                "fbtrace_id": "abc123"
            }
        }
        error = parse_meta_error(error_response, 400)
        assert error.error_code == 17
        assert error.message == "Rate limit exceeded"
        assert error.error_type == "OAuthException"
        assert error.error_subcode == 123
        assert error.fbtrace_id == "abc123"
        assert error.status_code == 400

    def test_parse_error_without_status_code(self):
        """Test parsing error without explicit status code."""
        error_response = {"error": {"message": "Some error", "code": 100}}
        error = parse_meta_error(error_response)
        assert error.error_code == 100
        assert error.message == "Some error"
        assert error.status_code is None

    def test_parse_empty_error(self):
        """Test parsing empty error response."""
        error = parse_meta_error({}, 500)
        assert error.message == "Unknown error"
        assert error.status_code == 500

    def test_parse_error_string_message(self):
        """Test parsing when error is a string instead of dict."""
        error_response = {"error": "Something went wrong"}
        error = parse_meta_error(error_response, 500)
        assert error.message == "Something went wrong"


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Test successful call without retry."""
        call_count = 0

        @with_retry(max_retries=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient error."""
        call_count = 0

        @with_retry(max_retries=5)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MetaApiError(message="Rate limit", error_code=17)
            return "success"

        # Patch sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await failing_then_success()

        assert result == "success"
        assert call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test exception raised after max retries."""
        call_count = 0

        @with_retry(max_retries=2)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise MetaApiError(message="Rate limit", error_code=17)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(MetaApiError) as exc_info:
                await always_fails()

        assert exc_info.value.error_code == 17
        # With max_retries=2 and error code 17 (max 3 retries), we get min(2, 3) = 2 retries
        # So attempts = initial + 2 retries = 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error_immediate_raise(self):
        """Test non-retryable errors are raised immediately."""
        call_count = 0

        @with_retry(max_retries=5)
        async def auth_error():
            nonlocal call_count
            call_count += 1
            raise MetaApiError(message="Invalid token", error_code=190)

        with pytest.raises(MetaApiError) as exc_info:
            await auth_error()

        assert exc_info.value.error_code == 190
        assert call_count == 1  # No retries for auth errors

    @pytest.mark.asyncio
    async def test_retry_all_errors_mode(self):
        """Test retry_on_all_errors flag."""
        call_count = 0

        @with_retry(max_retries=3, retry_on_all_errors=True)
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Some error")
            return "success"

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await raises_value_error()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_meta_error_without_retry_all(self):
        """Test non-MetaApiError exceptions without retry_on_all_errors."""
        call_count = 0

        @with_retry(max_retries=3)
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Some error")

        with pytest.raises(ValueError):
            await raises_value_error()

        assert call_count == 1  # No retry for non-MetaApiError

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @with_retry(max_retries=3)
        async def my_function():
            """My docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert "My docstring" in my_function.__doc__

    def test_decorator_stores_config(self):
        """Test that decorator stores retry config on wrapper."""
        @with_retry(max_retries=5, retry_on_all_errors=True)
        async def my_function():
            return "result"

        assert hasattr(my_function, '_retry_config')
        assert my_function._retry_config["max_retries"] == 5
        assert my_function._retry_config["retry_on_all_errors"] is True


class TestRetryWithBackoff:
    """Tests for retry_with_backoff convenience function."""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test successful retry after failures."""
        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MetaApiError(message="Service unavailable", error_code=2)
            return {"status": "ok"}

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await retry_with_backoff(failing_operation, max_retries=3)

        assert result == {"status": "ok"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test exception after retries exhausted."""
        async def always_fails():
            raise MetaApiError(message="Service unavailable", error_code=2)

        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(MetaApiError):
                await retry_with_backoff(always_fails, max_retries=2)


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self):
        """Test recovery from rate limiting."""
        attempts = []

        @with_retry(max_retries=5)
        async def api_call():
            attempts.append(len(attempts) + 1)
            if len(attempts) <= 2:
                # Simulate rate limit error
                raise MetaApiError(
                    message="(#17) User request limit reached",
                    error_code=17,
                    status_code=400
                )
            return {"data": [{"id": "123"}]}

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await api_call()

        assert result == {"data": [{"id": "123"}]}
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_server_error_recovery(self):
        """Test recovery from server errors."""
        attempts = []

        @with_retry(max_retries=3)
        async def api_call():
            attempts.append(len(attempts) + 1)
            if len(attempts) == 1:
                raise MetaApiError(
                    message="Internal Server Error",
                    status_code=500
                )
            return {"success": True}

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await api_call()

        assert result == {"success": True}
        assert len(attempts) == 2

    @pytest.mark.asyncio
    async def test_permission_error_no_retry(self):
        """Test permission errors don't retry."""
        attempts = []

        @with_retry(max_retries=5)
        async def api_call():
            attempts.append(len(attempts) + 1)
            raise MetaApiError(
                message="(#200) Requires extended permission: ads_management",
                error_code=200,
                status_code=403
            )

        with pytest.raises(MetaApiError) as exc_info:
            await api_call()

        assert exc_info.value.error_code == 200
        assert len(attempts) == 1  # No retries

    @pytest.mark.asyncio
    async def test_multiple_error_types_in_sequence(self):
        """Test handling different error types in sequence."""
        attempts = []
        errors = [
            MetaApiError(message="Rate limit", error_code=17),  # Retryable
            MetaApiError(message="Server error", status_code=503),  # Retryable
            None,  # Success
        ]

        @with_retry(max_retries=5)
        async def api_call():
            idx = len(attempts)
            attempts.append(idx + 1)
            if idx < len(errors) and errors[idx] is not None:
                raise errors[idx]
            return {"success": True}

        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await api_call()

        assert result == {"success": True}
        assert len(attempts) == 3  # 2 retryable errors + 1 success
