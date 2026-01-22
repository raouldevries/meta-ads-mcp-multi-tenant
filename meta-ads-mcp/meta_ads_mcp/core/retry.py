"""
Retry logic with exponential backoff for Meta API calls.

Handles transient errors (rate limits, server errors) automatically
with configurable retry counts and delays. Designed for production
multi-account scenarios where rate limits are common.

Usage:
    from .retry import with_retry, MetaApiError, ErrorAction

    @with_retry(max_retries=3)
    async def my_api_call():
        ...
"""

import asyncio
import random
import logging
from enum import Enum
from typing import Callable, TypeVar, Optional, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorAction(Enum):
    """Action to take for a Meta API error."""
    RETRY = "retry"           # Retry with backoff
    RATE_LIMIT = "rate_limit" # Record rate limit, block key temporarily
    AUTH_ERROR = "auth_error" # Token invalid, don't retry
    PERM_ERROR = "perm_error" # Permission denied, don't retry
    NOT_FOUND = "not_found"   # Resource doesn't exist
    BAD_REQUEST = "bad_req"   # Invalid parameters
    SERVER_ERROR = "server"   # Meta server error, retry
    UNKNOWN = "unknown"       # Unknown error

T = TypeVar('T')


class RetryConfig:
    """
    Configuration for retry behavior.

    Meta API error codes reference:
    https://developers.facebook.com/docs/marketing-api/error-reference
    """

    # Error codes that trigger retry with (max_retries, description)
    RETRYABLE_ERROR_CODES: dict[int, Tuple[int, str]] = {
        1: (3, "Unknown error - transient"),
        2: (3, "Service temporarily unavailable"),
        4: (3, "Application request limit reached"),
        17: (3, "User request limit reached"),
        32: (2, "Page request limit reached"),
        341: (2, "Application limit reached - temporary"),
        368: (2, "Temporarily blocked for policies"),
        613: (2, "Calls to this API have exceeded the rate limit"),
        80000: (3, "Too many calls from this ad account"),
        80001: (3, "Too many calls from this ad account"),
        80002: (3, "Too many calls to this Page"),
        80003: (2, "Too many calls from this ad-account"),
        80004: (3, "Too many calls from the caller"),
        80005: (2, "Too many calls from this location"),
        80006: (2, "Too many calls from this Page"),
        80008: (3, "User request limit reached"),
    }

    # HTTP status codes that trigger retry with (max_retries, description)
    RETRYABLE_HTTP_STATUS: dict[int, Tuple[int, str]] = {
        429: (3, "Too Many Requests"),
        500: (2, "Internal Server Error"),
        502: (2, "Bad Gateway"),
        503: (3, "Service Unavailable"),
        504: (2, "Gateway Timeout"),
    }

    # Error code to action mapping for classification
    ERROR_ACTIONS: dict[int, ErrorAction] = {
        # Rate limiting
        4: ErrorAction.RATE_LIMIT,
        17: ErrorAction.RATE_LIMIT,
        32: ErrorAction.RATE_LIMIT,
        341: ErrorAction.RATE_LIMIT,
        613: ErrorAction.RATE_LIMIT,
        80000: ErrorAction.RATE_LIMIT,
        80001: ErrorAction.RATE_LIMIT,
        80002: ErrorAction.RATE_LIMIT,
        80003: ErrorAction.RATE_LIMIT,
        80004: ErrorAction.RATE_LIMIT,
        80005: ErrorAction.RATE_LIMIT,
        80006: ErrorAction.RATE_LIMIT,
        80008: ErrorAction.RATE_LIMIT,
        # Auth errors
        190: ErrorAction.AUTH_ERROR,
        # Permission errors
        10: ErrorAction.PERM_ERROR,
        200: ErrorAction.PERM_ERROR,
        294: ErrorAction.PERM_ERROR,
        # Bad request
        100: ErrorAction.BAD_REQUEST,
        # Server errors (retryable)
        1: ErrorAction.SERVER_ERROR,
        2: ErrorAction.SERVER_ERROR,
        368: ErrorAction.RETRY,
    }

    # Backoff configuration
    INITIAL_DELAY_MS = 1000    # 1 second
    MAX_DELAY_MS = 60000       # 60 seconds
    JITTER_MAX_MS = 1000       # Up to 1 second random jitter
    BACKOFF_MULTIPLIER = 2     # Double delay each attempt

    @classmethod
    def is_retryable_error(cls, error_code: int) -> bool:
        """Check if Meta API error code is retryable."""
        return error_code in cls.RETRYABLE_ERROR_CODES

    @classmethod
    def is_retryable_status(cls, status_code: int) -> bool:
        """Check if HTTP status code is retryable."""
        return status_code in cls.RETRYABLE_HTTP_STATUS

    @classmethod
    def get_max_retries(cls, error_code: Optional[int] = None, status_code: Optional[int] = None) -> int:
        """Get maximum retry count for error."""
        if error_code and error_code in cls.RETRYABLE_ERROR_CODES:
            return cls.RETRYABLE_ERROR_CODES[error_code][0]
        if status_code and status_code in cls.RETRYABLE_HTTP_STATUS:
            return cls.RETRYABLE_HTTP_STATUS[status_code][0]
        return 0

    @classmethod
    def get_error_description(cls, error_code: Optional[int] = None, status_code: Optional[int] = None) -> str:
        """Get human-readable description for error."""
        if error_code and error_code in cls.RETRYABLE_ERROR_CODES:
            return cls.RETRYABLE_ERROR_CODES[error_code][1]
        if status_code and status_code in cls.RETRYABLE_HTTP_STATUS:
            return cls.RETRYABLE_HTTP_STATUS[status_code][1]
        return "Unknown error"

    @classmethod
    def get_action(cls, error_code: Optional[int] = None, status_code: Optional[int] = None) -> ErrorAction:
        """Get the recommended action for an error."""
        if error_code and error_code in cls.ERROR_ACTIONS:
            return cls.ERROR_ACTIONS[error_code]
        # HTTP status code based actions
        if status_code:
            if status_code == 401 or status_code == 403:
                return ErrorAction.AUTH_ERROR
            if status_code == 404:
                return ErrorAction.NOT_FOUND
            if status_code == 429:
                return ErrorAction.RATE_LIMIT
            if status_code >= 500:
                return ErrorAction.SERVER_ERROR
            if status_code >= 400:
                return ErrorAction.BAD_REQUEST
        return ErrorAction.UNKNOWN

    @classmethod
    def calculate_delay(cls, attempt: int, retry_after: Optional[int] = None) -> float:
        """
        Calculate delay before next retry using exponential backoff with jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            retry_after: Server-provided Retry-After header value in seconds

        Returns:
            Delay in seconds
        """
        # Honor server-provided Retry-After header if present
        if retry_after is not None and retry_after > 0:
            # Add small jitter even to server-provided delays
            jitter = random.randint(0, min(cls.JITTER_MAX_MS, 500)) / 1000.0
            return float(retry_after) + jitter

        # Exponential backoff: min(initial * multiplier^attempt, max) + jitter
        delay_ms = min(
            cls.INITIAL_DELAY_MS * (cls.BACKOFF_MULTIPLIER ** attempt),
            cls.MAX_DELAY_MS
        )
        jitter = random.randint(0, cls.JITTER_MAX_MS)
        return (delay_ms + jitter) / 1000.0


class MetaApiError(Exception):
    """
    Exception for Meta API errors with retry support.

    Captures all relevant error information from Meta API responses
    and provides retry intelligence.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        error_subcode: Optional[int] = None,
        error_type: Optional[str] = None,
        status_code: Optional[int] = None,
        retry_after: Optional[int] = None,
        fbtrace_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.error_type = error_type
        self.status_code = status_code
        self.retry_after = retry_after
        self.fbtrace_id = fbtrace_id

    @property
    def is_retryable(self) -> bool:
        """Check if this error should be retried."""
        return (
            (self.error_code is not None and RetryConfig.is_retryable_error(self.error_code))
            or (self.status_code is not None and RetryConfig.is_retryable_status(self.status_code))
        )

    @property
    def max_retries(self) -> int:
        """Get maximum retries for this error."""
        return RetryConfig.get_max_retries(self.error_code, self.status_code)

    @property
    def error_description(self) -> str:
        """Get human-readable error description."""
        return RetryConfig.get_error_description(self.error_code, self.status_code)

    @property
    def action(self) -> ErrorAction:
        """Get the recommended action for this error."""
        return RetryConfig.get_action(self.error_code, self.status_code)

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"code={self.error_code}")
        if self.error_subcode:
            parts.append(f"subcode={self.error_subcode}")
        if self.status_code:
            parts.append(f"http={self.status_code}")
        if self.fbtrace_id:
            parts.append(f"trace={self.fbtrace_id}")
        return " | ".join(parts)

    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON serialization."""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "error_subcode": self.error_subcode,
            "error_type": self.error_type,
            "status_code": self.status_code,
            "is_retryable": self.is_retryable,
            "action": self.action.value,
            "fbtrace_id": self.fbtrace_id
        }


def parse_meta_error(response_data: dict, status_code: Optional[int] = None) -> MetaApiError:
    """
    Parse Meta API error response into MetaApiError.

    Args:
        response_data: JSON response from Meta API containing 'error' key
        status_code: HTTP status code from response

    Returns:
        MetaApiError with parsed details
    """
    error = response_data.get("error", {})
    is_dict = isinstance(error, dict)

    # Extract retry-after from headers in error response
    retry_after = None
    if is_dict:
        headers = error.get("headers", {})
        if isinstance(headers, dict):
            retry_after_str = headers.get("Retry-After") or headers.get("retry-after")
            if retry_after_str:
                try:
                    retry_after = int(retry_after_str)
                except (ValueError, TypeError):
                    pass

    # Build error from dict fields or use string representation
    if is_dict:
        return MetaApiError(
            message=error.get("message", "Unknown error"),
            error_code=error.get("code"),
            error_subcode=error.get("error_subcode"),
            error_type=error.get("type"),
            status_code=status_code,
            retry_after=retry_after,
            fbtrace_id=error.get("fbtrace_id")
        )

    return MetaApiError(message=str(error), status_code=status_code)


def with_retry(max_retries: int = 3, retry_on_all_errors: bool = False):
    """
    Decorator for API calls with automatic retry on transient errors.

    Implements exponential backoff with jitter for rate limit handling.
    Only retries on known transient errors unless retry_on_all_errors=True.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        retry_on_all_errors: If True, retry on any error (default: False)

    Usage:
        @with_retry(max_retries=3)
        async def make_api_call(...):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except MetaApiError as e:
                    last_error = e

                    # Check if we should retry
                    effective_max_retries = min(max_retries, e.max_retries) if e.is_retryable else 0

                    if not e.is_retryable and not retry_on_all_errors:
                        logger.warning(
                            f"Non-retryable error in {func.__name__}: {e.message} "
                            f"(code={e.error_code})"
                        )
                        raise

                    if attempt >= effective_max_retries:
                        logger.error(
                            f"Max retries ({effective_max_retries}) exceeded for {func.__name__}: "
                            f"{e.message}"
                        )
                        raise

                    # Calculate delay
                    delay = RetryConfig.calculate_delay(attempt, e.retry_after)

                    logger.warning(
                        f"Retryable error in {func.__name__} "
                        f"(attempt {attempt + 1}/{effective_max_retries + 1}): "
                        f"{e.error_description} - {e.message}. "
                        f"Retrying in {delay:.1f}s"
                    )

                    await asyncio.sleep(delay)

                except Exception as e:
                    # Non-Meta errors
                    if retry_on_all_errors and attempt < max_retries:
                        delay = RetryConfig.calculate_delay(attempt)
                        logger.warning(
                            f"Error in {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): "
                            f"{str(e)}. Retrying in {delay:.1f}s"
                        )
                        last_error = e
                        await asyncio.sleep(delay)
                    else:
                        raise

            # Should not reach here, but just in case
            if last_error:
                raise last_error
            raise RuntimeError(f"Unexpected state in retry logic for {func.__name__}")

        # Store retry config on wrapper for introspection
        wrapper._retry_config = {"max_retries": max_retries, "retry_on_all_errors": retry_on_all_errors}
        return wrapper
    return decorator


# Convenience function for manual retry logic
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    *args,
    **kwargs
) -> T:
    """
    Execute a function with retry logic.

    For use when you can't use the decorator.

    Args:
        func: Async function to execute
        max_retries: Maximum retry attempts
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of func
    """
    @with_retry(max_retries=max_retries)
    async def wrapped():
        return await func(*args, **kwargs)

    return await wrapped()
