"""
Meta Graph API error classification and handling.

Maps Meta error codes to appropriate actions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorAction(Enum):
    """Action to take for an error."""
    RETRY = "retry"           # Retry with backoff
    RATE_LIMIT = "rate_limit" # Record rate limit, block key temporarily
    AUTH_ERROR = "auth_error" # Token invalid, don't retry
    PERM_ERROR = "perm_error" # Permission denied, don't retry
    NOT_FOUND = "not_found"   # Resource doesn't exist
    BAD_REQUEST = "bad_req"   # Invalid parameters
    SERVER_ERROR = "server"   # Meta server error, retry
    UNKNOWN = "unknown"       # Unknown error


@dataclass
class ErrorClassification:
    """Classification of a Meta API error."""
    code: int
    subcode: Optional[int]
    action: ErrorAction
    retryable: bool
    max_retries: int
    description: str


# Meta Graph API error code mapping
# Reference: https://developers.facebook.com/docs/graph-api/guides/error-handling
ERROR_MAP = {
    # OAuth errors (190.xxx)
    190: ErrorClassification(
        code=190,
        subcode=None,
        action=ErrorAction.AUTH_ERROR,
        retryable=False,
        max_retries=0,
        description="Invalid OAuth access token"
    ),

    # Rate limiting errors
    4: ErrorClassification(
        code=4,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=3,
        description="Application request limit reached"
    ),
    17: ErrorClassification(
        code=17,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=3,
        description="User request limit reached"
    ),
    32: ErrorClassification(
        code=32,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=2,
        description="Page request limit reached"
    ),
    613: ErrorClassification(
        code=613,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=2,
        description="Calls to this API have exceeded the rate limit"
    ),

    # Permission errors
    10: ErrorClassification(
        code=10,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="Permission denied"
    ),
    200: ErrorClassification(
        code=200,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="Permission error (requires extended permission)"
    ),
    294: ErrorClassification(
        code=294,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="App not whitelisted"
    ),

    # Bad request / Invalid parameter
    100: ErrorClassification(
        code=100,
        subcode=None,
        action=ErrorAction.BAD_REQUEST,
        retryable=False,
        max_retries=0,
        description="Invalid parameter"
    ),

    # Server errors
    1: ErrorClassification(
        code=1,
        subcode=None,
        action=ErrorAction.SERVER_ERROR,
        retryable=True,
        max_retries=3,
        description="Unknown error (Meta server issue)"
    ),
    2: ErrorClassification(
        code=2,
        subcode=None,
        action=ErrorAction.SERVER_ERROR,
        retryable=True,
        max_retries=3,
        description="Service temporarily unavailable"
    ),
}


def classify_error(error_code: int, error_subcode: Optional[int] = None) -> ErrorClassification:
    """
    Classify a Meta API error.

    Args:
        error_code: The error code from Meta's response
        error_subcode: Optional subcode for more specific errors

    Returns:
        ErrorClassification with action and retry info
    """
    # Check for exact match
    if error_code in ERROR_MAP:
        return ERROR_MAP[error_code]

    # Default classification
    return ErrorClassification(
        code=error_code,
        subcode=error_subcode,
        action=ErrorAction.UNKNOWN,
        retryable=False,
        max_retries=0,
        description=f"Unknown error code: {error_code}"
    )


class MetaApiError(Exception):
    """Exception for Meta API errors with classification."""

    def __init__(
        self,
        message: str,
        error_code: int,
        error_subcode: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.retry_after = retry_after
        self.classification = classify_error(error_code, error_subcode)
        super().__init__(message)

    @property
    def is_retryable(self) -> bool:
        return self.classification.retryable

    @property
    def action(self) -> ErrorAction:
        return self.classification.action

    @property
    def max_retries(self) -> int:
        return self.classification.max_retries

    def to_dict(self) -> dict:
        """Convert error to dictionary for JSON response."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "error_subcode": self.error_subcode,
            "action": self.action.value,
            "retryable": self.is_retryable,
            "retry_after": self.retry_after
        }
