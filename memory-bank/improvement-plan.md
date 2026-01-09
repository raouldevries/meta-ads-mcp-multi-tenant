# Meta Ads MCP Server - Improvement Plan

**Created:** 2026-01-08
**Source:** repo-comparison.md analysis
**Status:** Ready for implementation

---

## Table of Contents

1. [Priority Tier 1: Essential](#priority-tier-1-essential)
   - 1.1 Centralized Retry/Backoff
   - 1.2 Health Check Tool
   - 1.3 API v23.0 Upgrade
   - 1.4 Pagination Helpers
2. [Priority Tier 2: High Value](#priority-tier-2-high-value)
   - 2.1 Token Validation Tools
   - 2.2 Compare Entities Helper
   - 2.3 Default Limits & Presets
   - 2.4 Get Capabilities Tool
3. [Priority Tier 3: Nice-to-Have](#priority-tier-3-nice-to-have)
   - 3.1 Export to CSV/JSON
   - 3.2 Creative Validation Helpers

---

## Priority Tier 1: Essential

### 1.1 Centralized Retry/Backoff

**Why it matters:** Meta rate limits are aggressive. Without retry logic, temporary rate limits cause permanent failures. Users see cryptic errors instead of automatic recovery.

**Prerequisites:**
- None (foundational improvement)

**Complexity:** 4 steps

**Dependencies:** None

---

#### Step 1.1.1: Create the retry module file

**Action:** Create a new file for retry logic with exponential backoff

**Location:** `meta-ads-mcp/meta_ads_mcp/core/retry.py`

**Implementation:**
```python
"""
Retry logic with exponential backoff for Meta API calls.

Handles transient errors (rate limits, server errors) automatically
with configurable retry counts and delays.
"""

import asyncio
import random
import logging
from typing import Callable, TypeVar, Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""

    # Error codes that trigger retry with max retry counts
    RETRYABLE_CODES = {
        4: 3,      # Application request limit - 3 retries
        17: 3,     # User request limit - 3 retries
        32: 2,     # Page request limit - 2 retries
        613: 2,    # Calls limit reached - 2 retries
        80004: 3,  # Rate limit hit - 3 retries
    }

    # HTTP status codes that trigger retry
    RETRYABLE_HTTP_STATUS = {
        429: 3,    # Too Many Requests - 3 retries
        500: 2,    # Internal Server Error - 2 retries
        502: 2,    # Bad Gateway - 2 retries
        503: 3,    # Service Unavailable - 3 retries
        504: 2,    # Gateway Timeout - 2 retries
    }

    # Backoff configuration
    INITIAL_DELAY_MS = 1000
    MAX_DELAY_MS = 60000
    JITTER_MAX_MS = 1000

    @classmethod
    def is_retryable_error(cls, error_code: int) -> bool:
        """Check if error code is retryable."""
        return error_code in cls.RETRYABLE_CODES

    @classmethod
    def is_retryable_status(cls, status_code: int) -> bool:
        """Check if HTTP status is retryable."""
        return status_code in cls.RETRYABLE_HTTP_STATUS

    @classmethod
    def get_max_retries(cls, error_code: int = None, status_code: int = None) -> int:
        """Get maximum retry count for error."""
        if error_code and error_code in cls.RETRYABLE_CODES:
            return cls.RETRYABLE_CODES[error_code]
        if status_code and status_code in cls.RETRYABLE_HTTP_STATUS:
            return cls.RETRYABLE_HTTP_STATUS[status_code]
        return 0

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
        # Honor server-provided Retry-After header
        if retry_after is not None and retry_after > 0:
            return float(retry_after)

        # Exponential backoff: min(initial * 2^attempt, max) + jitter
        delay_ms = min(
            cls.INITIAL_DELAY_MS * (2 ** attempt),
            cls.MAX_DELAY_MS
        )
        jitter = random.randint(0, cls.JITTER_MAX_MS)
        return (delay_ms + jitter) / 1000.0


class MetaApiError(Exception):
    """Exception for Meta API errors with retry support."""

    def __init__(
        self,
        message: str,
        error_code: int = None,
        error_subcode: int = None,
        status_code: int = None,
        retry_after: int = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.status_code = status_code
        self.retry_after = retry_after

    @property
    def is_retryable(self) -> bool:
        """Check if this error should be retried."""
        if self.error_code and RetryConfig.is_retryable_error(self.error_code):
            return True
        if self.status_code and RetryConfig.is_retryable_status(self.status_code):
            return True
        return False

    @property
    def max_retries(self) -> int:
        """Get maximum retries for this error."""
        return RetryConfig.get_max_retries(self.error_code, self.status_code)


def with_retry(max_retries: int = 3):
    """
    Decorator for API calls with automatic retry on transient errors.

    Usage:
        @with_retry(max_retries=3)
        async def make_api_call(...):
            ...

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except MetaApiError as e:
                    last_error = e

                    # Check if we should retry
                    if not e.is_retryable or attempt >= e.max_retries:
                        raise

                    # Calculate delay
                    delay = RetryConfig.calculate_delay(attempt, e.retry_after)

                    logger.warning(
                        f"API call failed (attempt {attempt + 1}/{e.max_retries + 1}), "
                        f"error_code={e.error_code}, retrying in {delay:.1f}s: {e.message}"
                    )

                    await asyncio.sleep(delay)

                except Exception as e:
                    # Non-Meta errors are not retried
                    raise

            # Should not reach here, but just in case
            if last_error:
                raise last_error

        return wrapper
    return decorator


def parse_meta_error(response_data: dict, status_code: int = None) -> MetaApiError:
    """
    Parse Meta API error response into MetaApiError.

    Args:
        response_data: JSON response from Meta API
        status_code: HTTP status code

    Returns:
        MetaApiError with parsed details
    """
    error = response_data.get("error", {})

    return MetaApiError(
        message=error.get("message", "Unknown error"),
        error_code=error.get("code"),
        error_subcode=error.get("error_subcode"),
        status_code=status_code,
        retry_after=error.get("headers", {}).get("Retry-After")
    )
```

**Verification:**
```bash
cd meta-ads-mcp
source venv/bin/activate
python -c "from meta_ads_mcp.core.retry import with_retry, RetryConfig; print('Retry module loaded successfully')"
```

**Audit Fix Sub-steps:**
- Update `with_retry` to cap retries with `min(max_retries, e.max_retries)` and use that for attempt comparisons/logs.
- Extend `parse_meta_error` to accept response headers and honor `Retry-After` from headers.

---

#### Step 1.1.2: Add retry module to core exports

**Action:** Export the retry module from core/__init__.py

**Location:** `meta-ads-mcp/meta_ads_mcp/core/__init__.py`

**Implementation:**
```python
# Add this import near the top with other imports
from .retry import with_retry, RetryConfig, MetaApiError, parse_meta_error
```

**Verification:**
```bash
python -c "from meta_ads_mcp.core import with_retry; print('Export successful')"
```

---

#### Step 1.1.3: Integrate retry into API client

**Action:** Update the make_api_request function to use retry logic

**Location:** `meta-ads-mcp/meta_ads_mcp/core/api.py`

**Implementation:**

Find the `make_api_request` function and wrap it with retry logic:

```python
# Add import at top of file
from .retry import with_retry, MetaApiError, parse_meta_error

# Modify the make_api_request function
@with_retry(max_retries=3)
async def make_api_request(
    endpoint: str,
    params: dict = None,
    method: str = "GET",
    access_token: str = None,
    # ... existing parameters
) -> dict:
    """Make API request with automatic retry on transient errors."""

    # ... existing implementation ...

    # When handling error responses, raise MetaApiError instead of returning error dict
    if "error" in response_data:
        error = parse_meta_error(response_data, response.status_code)
        if error.is_retryable:
            raise error
        # Non-retryable errors still return as before for backward compatibility
        return response_data
```

**Verification:**
```bash
python -m pytest tests/test_api.py -v -k "retry" 2>/dev/null || echo "Add retry tests in step 1.1.4"
```

**Audit Fix Sub-steps:**
- Raise `MetaApiError` for retryable HTTP status codes even when response bodies lack `"error"`.
- Wrap network/timeout exceptions into retryable errors.
- Pass response headers into `parse_meta_error` so `Retry-After` is honored.

---

#### Step 1.1.4: Add retry unit tests

**Action:** Create unit tests for retry logic

**Location:** `meta-ads-mcp/tests/test_retry.py`

**Implementation:**
```python
"""Tests for retry logic."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from meta_ads_mcp.core.retry import (
    RetryConfig,
    MetaApiError,
    with_retry,
    parse_meta_error
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_retryable_error_codes(self):
        """Test that known error codes are retryable."""
        assert RetryConfig.is_retryable_error(4) is True  # App limit
        assert RetryConfig.is_retryable_error(17) is True  # User limit
        assert RetryConfig.is_retryable_error(190) is False  # Auth error

    def test_retryable_http_status(self):
        """Test that 429 and 5xx are retryable."""
        assert RetryConfig.is_retryable_status(429) is True
        assert RetryConfig.is_retryable_status(500) is True
        assert RetryConfig.is_retryable_status(400) is False
        assert RetryConfig.is_retryable_status(401) is False

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        delay_0 = RetryConfig.calculate_delay(0)
        delay_1 = RetryConfig.calculate_delay(1)
        delay_2 = RetryConfig.calculate_delay(2)

        # Each delay should roughly double (with jitter)
        assert 1.0 <= delay_0 <= 2.0
        assert 2.0 <= delay_1 <= 3.0
        assert 4.0 <= delay_2 <= 5.0

    def test_calculate_delay_respects_retry_after(self):
        """Test that Retry-After header is honored."""
        delay = RetryConfig.calculate_delay(0, retry_after=30)
        assert delay == 30.0


class TestMetaApiError:
    """Tests for MetaApiError."""

    def test_retryable_error(self):
        """Test error with retryable code."""
        error = MetaApiError("Rate limited", error_code=4)
        assert error.is_retryable is True
        assert error.max_retries == 3

    def test_non_retryable_error(self):
        """Test error with non-retryable code."""
        error = MetaApiError("Invalid token", error_code=190)
        assert error.is_retryable is False
        assert error.max_retries == 0


class TestWithRetry:
    """Tests for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_success_no_retry(self):
        """Test successful call doesn't retry."""
        call_count = 0

        @with_retry(max_retries=3)
        async def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_call()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient error."""
        call_count = 0

        @with_retry(max_retries=3)
        async def flaky_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MetaApiError("Rate limited", error_code=4)
            return "success"

        with patch('meta_ads_mcp.core.retry.asyncio.sleep', new_callable=AsyncMock):
            result = await flaky_call()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error(self):
        """Test no retry on authentication error."""
        call_count = 0

        @with_retry(max_retries=3)
        async def auth_error_call():
            nonlocal call_count
            call_count += 1
            raise MetaApiError("Invalid token", error_code=190)

        with pytest.raises(MetaApiError):
            await auth_error_call()

        assert call_count == 1  # No retries
```

**Verification:**
```bash
python -m pytest tests/test_retry.py -v
```

---

### 1.2 Health Check Tool

**Why it matters:** Validates token and API connectivity in 30 seconds. Saves hours of debugging cryptic auth errors. Essential for production monitoring.

**Prerequisites:**
- None

**Complexity:** 2 steps

**Dependencies:** None

---

#### Step 1.2.1: Create health check tool

**Action:** Add a health_check tool to validate API connectivity

**Location:** `meta-ads-mcp/meta_ads_mcp/core/accounts.py`

**Implementation:**

Add this function after the existing account tools:

```python
@mcp_server.tool()
async def health_check(
    access_token: Optional[str] = None
) -> str:
    """
    Validate Meta API connectivity and token status.

    Performs:
    1. Token validation (checks if token is valid)
    2. Permission check (lists accessible ad accounts)
    3. API latency measurement

    Returns:
        JSON with health status, token info, and diagnostics
    """
    import time
    from ..core.auth import get_current_access_token

    start_time = time.time()
    result = {
        "status": "unknown",
        "checks": {},
        "diagnostics": {}
    }

    try:
        # Get token
        token = access_token or await get_current_access_token()
        if not token:
            result["status"] = "error"
            result["checks"]["token"] = {
                "status": "failed",
                "message": "No access token configured"
            }
            return json.dumps(result, indent=2)

        result["checks"]["token"] = {
            "status": "present",
            "prefix": token[:20] + "..." if len(token) > 20 else token
        }

        # Test API connectivity with debug_token call
        token_check_start = time.time()
        try:
            debug_url = f"https://graph.facebook.com/v22.0/debug_token"
            params = {
                "input_token": token,
                "access_token": token
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(debug_url, params=params) as response:
                    token_data = await response.json()

            token_check_time = time.time() - token_check_start

            if "data" in token_data:
                data = token_data["data"]
                result["checks"]["token_validation"] = {
                    "status": "valid" if data.get("is_valid") else "invalid",
                    "app_id": data.get("app_id"),
                    "type": data.get("type"),
                    "expires_at": data.get("expires_at", 0),
                    "scopes": data.get("scopes", []),
                    "latency_ms": round(token_check_time * 1000)
                }
            else:
                result["checks"]["token_validation"] = {
                    "status": "error",
                    "error": token_data.get("error", {}).get("message", "Unknown error")
                }

        except Exception as e:
            result["checks"]["token_validation"] = {
                "status": "error",
                "error": str(e)
            }

        # Test ad accounts access
        accounts_start = time.time()
        try:
            accounts_url = "https://graph.facebook.com/v22.0/me/adaccounts"
            params = {
                "access_token": token,
                "fields": "id,name,account_status",
                "limit": 5
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(accounts_url, params=params) as response:
                    accounts_data = await response.json()

            accounts_time = time.time() - accounts_start

            if "data" in accounts_data:
                result["checks"]["ad_accounts"] = {
                    "status": "accessible",
                    "count": len(accounts_data["data"]),
                    "sample": [
                        {"id": acc["id"], "name": acc.get("name", "N/A")}
                        for acc in accounts_data["data"][:3]
                    ],
                    "latency_ms": round(accounts_time * 1000)
                }
            else:
                result["checks"]["ad_accounts"] = {
                    "status": "error",
                    "error": accounts_data.get("error", {}).get("message", "Unknown error")
                }

        except Exception as e:
            result["checks"]["ad_accounts"] = {
                "status": "error",
                "error": str(e)
            }

        # Determine overall status
        token_ok = result["checks"].get("token_validation", {}).get("status") == "valid"
        accounts_ok = result["checks"].get("ad_accounts", {}).get("status") == "accessible"

        if token_ok and accounts_ok:
            result["status"] = "healthy"
        elif token_ok:
            result["status"] = "degraded"
        else:
            result["status"] = "unhealthy"

        # Add diagnostics
        total_time = time.time() - start_time
        result["diagnostics"] = {
            "total_latency_ms": round(total_time * 1000),
            "api_version": "v22.0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return json.dumps(result, indent=2)
```

**Verification:**
```bash
# Restart MCP server, then test with Claude:
# "Run health check on Meta Ads API"
```

**Audit Fix Sub-steps:**
- Replace `aiohttp` usage with `httpx` and add explicit timeouts.
- Use `get_api_base_url()`/`get_api_version()` instead of hardcoded `v22.0`.
- Use app access token for `debug_token` or document the requirement explicitly.

---

#### Step 1.2.2: Add health check test

**Action:** Create test for health_check tool

**Location:** `meta-ads-mcp/tests/test_accounts.py`

**Implementation:**

Add to existing test file:

```python
@pytest.mark.e2e
async def test_health_check():
    """Test health_check tool returns valid status."""
    from meta_ads_mcp.core.accounts import health_check

    result = await health_check()
    data = json.loads(result)

    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy", "error"]
    assert "checks" in data
    assert "diagnostics" in data
```

**Verification:**
```bash
python -m pytest tests/test_accounts.py -v -k "health_check" -m e2e
```

**Audit Fix Sub-steps:**
- Decide whether this is a unit test or e2e test.
- If unit: mock HTTP calls and remove the `e2e` marker.
- If e2e: document required env vars and add skip conditions.

---

### 1.3 API v23.0 Upgrade

**Why it matters:** v22.0 deprecation is coming. Upgrading ensures continued API access and access to new features.

**Prerequisites:**
- Review Meta API changelog for v23.0 breaking changes

**Complexity:** 3 steps

**Dependencies:** None

---

#### Step 1.3.1: Create API version configuration

**Action:** Make API version configurable via environment variable

**Location:** `meta-ads-mcp/meta_ads_mcp/core/api.py`

**Implementation:**

Add near the top of the file:

```python
import os

# API Version Configuration
# Can be overridden via META_API_VERSION environment variable
DEFAULT_API_VERSION = "v23.0"
API_VERSION = os.environ.get("META_API_VERSION", DEFAULT_API_VERSION)

def get_api_base_url() -> str:
    """Get the Meta Graph API base URL with configured version."""
    return f"https://graph.facebook.com/{API_VERSION}"
```

**Verification:**
```bash
python -c "from meta_ads_mcp.core.api import API_VERSION; print(f'API Version: {API_VERSION}')"
```

---

#### Step 1.3.2: Update all hardcoded API URLs

**Action:** Replace hardcoded v22.0 references with configurable version

**Location:** Multiple files in `meta-ads-mcp/meta_ads_mcp/core/`

**Implementation:**

Use search and replace across all core files:

```bash
# Find all hardcoded v22.0 references
grep -r "graph.facebook.com/v22.0" meta_ads_mcp/core/

# Replace with the configurable version
# In each file, add import and update URLs:
```

For each file with hardcoded URLs:

```python
# Add import at top
from .api import get_api_base_url, API_VERSION

# Replace hardcoded URLs like:
# OLD: url = "https://graph.facebook.com/v22.0/..."
# NEW: url = f"{get_api_base_url()}/..."
```

**Verification:**
```bash
# Should return no results after fix
grep -r "graph.facebook.com/v22" meta_ads_mcp/core/ | grep -v "API_VERSION"
```

---

#### Step 1.3.3: Document API version configuration

**Action:** Add documentation for API version configuration

**Location:** `meta-ads-mcp/README.md`

**Implementation:**

Add to the Environment Variables section:

```markdown
### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `META_API_VERSION` | Meta Graph API version | `v23.0` |

**Example:**
```bash
# Use specific API version
export META_API_VERSION=v23.0
```
```

**Verification:**
```bash
cat meta-ads-mcp/README.md | grep -A5 "META_API_VERSION"
```

---

### 1.4 Pagination Helpers

**Why it matters:** Large accounts need to fetch all results. Without pagination helpers, users must manually handle cursors across multiple calls.

**Prerequisites:**
- Understanding of Meta API cursor-based pagination

**Complexity:** 3 steps

**Dependencies:** None

---

#### Step 1.4.1: Create pagination helper module

**Action:** Create a pagination utility for fetching all pages

**Location:** `meta-ads-mcp/meta_ads_mcp/core/pagination.py`

**Implementation:**
```python
"""
Pagination helpers for Meta API responses.

Provides utilities for:
- Fetching all pages automatically
- Configurable page limits
- Generator-based iteration for memory efficiency
"""

import logging
from typing import AsyncGenerator, Dict, List, Optional, Callable, Any
import aiohttp

logger = logging.getLogger(__name__)


class PaginationConfig:
    """Configuration for pagination behavior."""

    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100
    MAX_PAGES = 100  # Safety limit
    MAX_ITEMS = 10000  # Safety limit


async def fetch_all_pages(
    initial_url: str,
    params: Dict[str, Any],
    access_token: str,
    max_pages: int = PaginationConfig.MAX_PAGES,
    max_items: int = PaginationConfig.MAX_ITEMS,
    data_key: str = "data"
) -> List[Dict]:
    """
    Fetch all pages from a paginated Meta API endpoint.

    Args:
        initial_url: The API endpoint URL
        params: Query parameters (should include 'fields')
        access_token: Meta API access token
        max_pages: Maximum number of pages to fetch (default: 100)
        max_items: Maximum total items to fetch (default: 10000)
        data_key: Key in response containing data array (default: "data")

    Returns:
        List of all items across all pages

    Example:
        items = await fetch_all_pages(
            "https://graph.facebook.com/v23.0/act_123/campaigns",
            {"fields": "id,name,status"},
            access_token,
            max_pages=10
        )
    """
    all_items = []
    current_url = initial_url
    current_params = {**params, "access_token": access_token}
    pages_fetched = 0

    async with aiohttp.ClientSession() as session:
        while current_url and pages_fetched < max_pages and len(all_items) < max_items:
            try:
                async with session.get(current_url, params=current_params) as response:
                    data = await response.json()

                if "error" in data:
                    logger.error(f"Pagination error: {data['error']}")
                    break

                # Extract items from response
                items = data.get(data_key, [])
                all_items.extend(items)
                pages_fetched += 1

                logger.debug(
                    f"Fetched page {pages_fetched}: {len(items)} items "
                    f"(total: {len(all_items)})"
                )

                # Check for next page
                paging = data.get("paging", {})
                next_url = paging.get("next")

                if next_url:
                    # Next URL includes all params, so clear current_params
                    current_url = next_url
                    current_params = {}
                else:
                    break

            except Exception as e:
                logger.error(f"Pagination fetch error: {e}")
                break

    logger.info(f"Pagination complete: {len(all_items)} items from {pages_fetched} pages")
    return all_items


async def paginate_generator(
    initial_url: str,
    params: Dict[str, Any],
    access_token: str,
    max_pages: int = PaginationConfig.MAX_PAGES,
    data_key: str = "data"
) -> AsyncGenerator[Dict, None]:
    """
    Generator-based pagination for memory-efficient iteration.

    Yields items one at a time instead of loading all into memory.

    Args:
        initial_url: The API endpoint URL
        params: Query parameters
        access_token: Meta API access token
        max_pages: Maximum pages to fetch
        data_key: Key containing data array

    Yields:
        Individual items from each page

    Example:
        async for campaign in paginate_generator(url, params, token):
            process(campaign)
    """
    current_url = initial_url
    current_params = {**params, "access_token": access_token}
    pages_fetched = 0

    async with aiohttp.ClientSession() as session:
        while current_url and pages_fetched < max_pages:
            try:
                async with session.get(current_url, params=current_params) as response:
                    data = await response.json()

                if "error" in data:
                    logger.error(f"Pagination error: {data['error']}")
                    return

                # Yield items one at a time
                for item in data.get(data_key, []):
                    yield item

                pages_fetched += 1

                # Get next page URL
                paging = data.get("paging", {})
                next_url = paging.get("next")

                if next_url:
                    current_url = next_url
                    current_params = {}
                else:
                    return

            except Exception as e:
                logger.error(f"Pagination generator error: {e}")
                return


def add_pagination_params(
    params: Dict[str, Any],
    limit: int = PaginationConfig.DEFAULT_PAGE_SIZE,
    after: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add pagination parameters to a request.

    Args:
        params: Existing parameters dict
        limit: Page size (default: 25, max: 100)
        after: Cursor for next page (optional)

    Returns:
        Updated params dict with pagination
    """
    result = {**params}
    result["limit"] = min(limit, PaginationConfig.MAX_PAGE_SIZE)

    if after:
        result["after"] = after

    return result
```

**Verification:**
```bash
python -c "from meta_ads_mcp.core.pagination import fetch_all_pages; print('Pagination module loaded')"
```

**Audit Fix Sub-steps:**
- Implement pagination using `httpx` or reuse `make_api_request` to keep auth/retry consistent.
- Add explicit timeouts to pagination requests.

---

#### Step 1.4.2: Add fetch_all parameter to list tools

**Action:** Update get_campaigns to support fetching all pages

**Location:** `meta-ads-mcp/meta_ads_mcp/core/campaigns.py`

**Implementation:**

Update the get_campaigns function signature and implementation:

```python
from .pagination import fetch_all_pages, add_pagination_params

@mcp_server.tool()
@meta_api_tool
async def get_campaigns(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 10,
    status_filter: str = "",
    objective_filter: Union[str, List[str]] = "",
    after: str = "",
    fetch_all: bool = False,  # NEW PARAMETER
) -> str:
    """
    Get campaigns for a Meta Ads account with optional filtering.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        limit: Maximum campaigns per page (default: 10, max: 100)
        status_filter: Filter by status (ACTIVE, PAUSED, ARCHIVED)
        objective_filter: Filter by objective(s)
        after: Pagination cursor for next page
        fetch_all: If True, fetch all pages automatically (default: False)

    Returns:
        JSON with campaigns and pagination info
    """
    # ... existing setup code ...

    if fetch_all:
        # Use pagination helper to fetch all campaigns
        all_campaigns = await fetch_all_pages(
            url,
            params,
            access_token,
            max_pages=50,  # Safety limit for campaigns
            max_items=5000
        )
        return json.dumps({
            "data": all_campaigns,
            "total_count": len(all_campaigns),
            "fetched_all": True
        }, indent=2)
    else:
        # Existing single-page behavior
        # ... existing implementation ...
```

**Verification:**
```bash
# Test with Claude: "Get all campaigns for account act_XXX with fetch_all=true"
```

**Audit Fix Sub-steps:**
- Define URL construction explicitly using `get_api_base_url()` and endpoint path.
- Resolve `access_token` when absent (use cached token helper).
- Return `pagination_info` metadata in the `fetch_all` response.

---

#### Step 1.4.3: Add pagination tests

**Action:** Create tests for pagination helpers

**Location:** `meta-ads-mcp/tests/test_pagination.py`

**Implementation:**
```python
"""Tests for pagination helpers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from meta_ads_mcp.core.pagination import (
    fetch_all_pages,
    paginate_generator,
    add_pagination_params,
    PaginationConfig
)


class TestAddPaginationParams:
    """Tests for add_pagination_params."""

    def test_default_limit(self):
        """Test default page size is applied."""
        result = add_pagination_params({})
        assert result["limit"] == PaginationConfig.DEFAULT_PAGE_SIZE

    def test_custom_limit(self):
        """Test custom limit is applied."""
        result = add_pagination_params({}, limit=50)
        assert result["limit"] == 50

    def test_max_limit_enforced(self):
        """Test limit is capped at max."""
        result = add_pagination_params({}, limit=500)
        assert result["limit"] == PaginationConfig.MAX_PAGE_SIZE

    def test_after_cursor(self):
        """Test after cursor is added."""
        result = add_pagination_params({}, after="cursor123")
        assert result["after"] == "cursor123"

    def test_preserves_existing_params(self):
        """Test existing params are preserved."""
        result = add_pagination_params({"fields": "id,name"}, limit=25)
        assert result["fields"] == "id,name"
        assert result["limit"] == 25
```

**Verification:**
```bash
python -m pytest tests/test_pagination.py -v
```

**Audit Fix Sub-steps:**
- Add tests for `fetch_all_pages` multi-page behavior with mocked responses.
- Add tests for `paginate_generator` iteration and error handling.
- Add tests for max page/item limits.

---

## Priority Tier 2: High Value

### 2.1 Token Validation Tools

**Why it matters:** Prevents cryptic auth errors by providing clear token status information. Essential for debugging permission issues.

**Prerequisites:**
- Health check tool (1.2) provides foundation

**Complexity:** 1 step

**Dependencies:** 1.2 Health Check Tool

---

#### Step 2.1.1: Create get_token_info tool

**Action:** Add tool to retrieve detailed token information

**Location:** `meta-ads-mcp/meta_ads_mcp/core/auth.py`

**Implementation:**

Add after existing auth functions:

```python
@mcp_server.tool()
async def get_token_info(
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about the current access token.

    Returns:
        JSON with token details including:
        - Token type (user, page, app)
        - Associated app ID
        - Granted permissions/scopes
        - Expiration time
        - User/page ID
    """
    token = access_token or await get_current_access_token()

    if not token:
        return json.dumps({
            "error": "No access token configured",
            "help": "Set META_ACCESS_TOKEN environment variable or configure OAuth"
        })

    try:
        url = f"https://graph.facebook.com/{API_VERSION}/debug_token"
        params = {
            "input_token": token,
            "access_token": token
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

        if "error" in data:
            return json.dumps({
                "error": data["error"].get("message", "Unknown error"),
                "error_code": data["error"].get("code")
            })

        token_data = data.get("data", {})

        # Format expiration time
        expires_at = token_data.get("expires_at", 0)
        if expires_at == 0:
            expiration = "Never (long-lived token)"
        else:
            import datetime
            exp_date = datetime.datetime.fromtimestamp(expires_at)
            remaining = exp_date - datetime.datetime.now()
            expiration = {
                "timestamp": expires_at,
                "date": exp_date.isoformat(),
                "remaining_days": remaining.days,
                "remaining_hours": remaining.seconds // 3600
            }

        return json.dumps({
            "is_valid": token_data.get("is_valid", False),
            "type": token_data.get("type", "unknown"),
            "app_id": token_data.get("app_id"),
            "user_id": token_data.get("user_id"),
            "scopes": token_data.get("scopes", []),
            "granular_scopes": token_data.get("granular_scopes", []),
            "expiration": expiration,
            "issued_at": token_data.get("issued_at"),
            "profile_id": token_data.get("profile_id"),
            "token_prefix": token[:20] + "..." if len(token) > 20 else token
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp_server.tool()
async def validate_token(
    access_token: Optional[str] = None
) -> str:
    """
    Quick validation check for access token.

    Returns simple pass/fail with actionable message.
    """
    token = access_token or await get_current_access_token()

    if not token:
        return json.dumps({
            "valid": False,
            "message": "No token configured",
            "action": "Set META_ACCESS_TOKEN or run OAuth flow"
        })

    try:
        # Quick test with minimal API call
        url = f"https://graph.facebook.com/{API_VERSION}/me"
        params = {"access_token": token, "fields": "id"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

        if "error" in data:
            error = data["error"]
            code = error.get("code", 0)

            # Provide actionable messages for common errors
            actions = {
                190: "Token expired or invalid. Generate new token.",
                102: "Session expired. Re-authenticate.",
                4: "Rate limit hit. Wait and retry.",
                17: "User rate limit. Wait and retry.",
            }

            return json.dumps({
                "valid": False,
                "error_code": code,
                "message": error.get("message"),
                "action": actions.get(code, "Check token and permissions")
            })

        return json.dumps({
            "valid": True,
            "user_id": data.get("id"),
            "message": "Token is valid and working"
        })

    except Exception as e:
        return json.dumps({
            "valid": False,
            "message": str(e),
            "action": "Check network connectivity"
        })
```

**Verification:**
```bash
# Test with Claude: "Get token info" or "Validate my Meta token"
```

**Audit Fix Sub-steps:**
- Use `httpx` instead of `aiohttp` and add explicit timeouts.
- Import `get_api_base_url()`/`get_api_version()` for URL construction.
- Use app access token for `debug_token` or document requirements clearly.

---

### 2.2 Compare Entities Helper

**Why it matters:** A/B testing is core to ads optimization. Comparing campaigns/ads side-by-side with computed deltas saves significant manual effort.

**Prerequisites:**
- get_insights tool working

**Complexity:** 1 step

**Dependencies:** None

---

#### Step 2.2.1: Create compare_entities tool

**Action:** Add tool for comparing campaigns, ad sets, or ads

**Location:** `meta-ads-mcp/meta_ads_mcp/core/insights.py`

**Implementation:**

Add after existing insight tools:

```python
@mcp_server.tool()
@meta_api_tool
async def compare_entities(
    entity_type: str,
    entity_ids: List[str],
    time_range: Union[str, Dict[str, str]] = "last_7d",
    metrics: Optional[List[str]] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Compare performance metrics across multiple campaigns, ad sets, or ads.

    Args:
        entity_type: Type of entity (campaign, adset, ad)
        entity_ids: List of IDs to compare (max 10)
        time_range: Time period for comparison (default: last_7d)
        metrics: Metrics to compare (default: spend, impressions, clicks, ctr, cpc)

    Returns:
        JSON with side-by-side comparison and rankings

    Example:
        compare_entities(
            entity_type="campaign",
            entity_ids=["123", "456", "789"],
            time_range="last_30d"
        )
    """
    # Limit to 10 entities for manageable output
    if len(entity_ids) > 10:
        return json.dumps({
            "error": "Maximum 10 entities can be compared at once",
            "provided": len(entity_ids)
        })

    # Default metrics if not specified
    if not metrics:
        metrics = [
            "spend", "impressions", "reach", "clicks",
            "ctr", "cpc", "cpm", "frequency"
        ]

    # Fetch insights for each entity
    results = []
    for entity_id in entity_ids:
        try:
            # Use existing get_insights function
            insight_result = await get_insights(
                object_id=entity_id,
                time_range=time_range,
                level=entity_type,
                limit=1,
                access_token=access_token
            )
            insight_data = json.loads(insight_result)

            if "data" in insight_data and insight_data["data"]:
                data = insight_data["data"][0]
                results.append({
                    "id": entity_id,
                    "name": data.get(f"{entity_type}_name", data.get("ad_name", entity_id)),
                    "metrics": {m: data.get(m, "N/A") for m in metrics}
                })
            else:
                results.append({
                    "id": entity_id,
                    "name": entity_id,
                    "error": "No data available"
                })

        except Exception as e:
            results.append({
                "id": entity_id,
                "error": str(e)
            })

    # Calculate rankings for numeric metrics
    rankings = {}
    for metric in metrics:
        values = []
        for r in results:
            if "metrics" in r and r["metrics"].get(metric) not in [None, "N/A"]:
                try:
                    val = float(str(r["metrics"][metric]).replace(",", ""))
                    values.append((r["id"], val))
                except (ValueError, TypeError):
                    pass

        if values:
            # Sort descending (higher is better for most metrics)
            # Exception: CPC, CPM lower is better
            reverse = metric not in ["cpc", "cpm", "frequency"]
            sorted_values = sorted(values, key=lambda x: x[1], reverse=reverse)
            rankings[metric] = {
                "best": sorted_values[0][0] if sorted_values else None,
                "worst": sorted_values[-1][0] if sorted_values else None,
                "ranking": [v[0] for v in sorted_values]
            }

    # Calculate deltas from average
    averages = {}
    for metric in metrics:
        values = []
        for r in results:
            if "metrics" in r and r["metrics"].get(metric) not in [None, "N/A"]:
                try:
                    values.append(float(str(r["metrics"][metric]).replace(",", "")))
                except (ValueError, TypeError):
                    pass
        if values:
            averages[metric] = sum(values) / len(values)

    # Add delta from average to each result
    for r in results:
        if "metrics" in r:
            r["delta_from_avg"] = {}
            for metric in metrics:
                if metric in averages and r["metrics"].get(metric) not in [None, "N/A"]:
                    try:
                        val = float(str(r["metrics"][metric]).replace(",", ""))
                        avg = averages[metric]
                        if avg > 0:
                            delta_pct = ((val - avg) / avg) * 100
                            r["delta_from_avg"][metric] = f"{delta_pct:+.1f}%"
                    except (ValueError, TypeError):
                        pass

    return json.dumps({
        "comparison": {
            "entity_type": entity_type,
            "time_range": time_range,
            "metrics": metrics,
            "entity_count": len(results)
        },
        "entities": results,
        "rankings": rankings,
        "averages": {k: round(v, 2) for k, v in averages.items()}
    }, indent=2)
```

**Verification:**
```bash
# Test with Claude: "Compare campaigns 123, 456, 789 for the last 30 days"
```

---

### 2.3 Default Limits & Presets

**Why it matters:** Prevents context window overflow with large responses. Provides sensible defaults that work well with LLMs.

**Prerequisites:**
- None

**Complexity:** 2 steps

**Dependencies:** None

---

#### Step 2.3.1: Create field presets module

**Action:** Create a module with field presets for common use cases

**Location:** `meta-ads-mcp/meta_ads_mcp/core/presets.py`

**Implementation:**
```python
"""
Field presets for Meta Ads API requests.

Provides pre-defined field sets optimized for different use cases,
reducing verbose field specifications and ensuring consistent responses.
"""

from typing import List, Dict

# Insight field presets
INSIGHT_PRESETS: Dict[str, List[str]] = {
    "basic": [
        "campaign_name", "adset_name", "ad_name",
        "spend", "impressions", "reach", "clicks"
    ],
    "efficiency": [
        "campaign_name", "adset_name", "ad_name",
        "spend", "impressions", "clicks",
        "ctr", "cpc", "cpm", "frequency"
    ],
    "conversions": [
        "campaign_name", "adset_name", "ad_name",
        "spend", "impressions", "clicks",
        "actions", "action_values", "cost_per_action_type",
        "purchase_roas", "website_purchase_roas"
    ],
    "video": [
        "campaign_name", "adset_name", "ad_name",
        "spend", "impressions", "reach",
        "video_p25_watched_actions", "video_p50_watched_actions",
        "video_p75_watched_actions", "video_p100_watched_actions",
        "video_thruplay_watched_actions"
    ],
    "full": [
        "account_id", "account_name",
        "campaign_id", "campaign_name",
        "adset_id", "adset_name",
        "ad_id", "ad_name",
        "spend", "impressions", "reach", "clicks",
        "ctr", "cpc", "cpm", "cpp", "frequency",
        "actions", "action_values", "cost_per_action_type",
        "conversions", "conversion_values", "cost_per_conversion",
        "video_p25_watched_actions", "video_p50_watched_actions",
        "video_p75_watched_actions", "video_p100_watched_actions",
        "video_thruplay_watched_actions"
    ]
}

# Campaign field presets
CAMPAIGN_PRESETS: Dict[str, List[str]] = {
    "basic": ["id", "name", "status", "objective"],
    "full": [
        "id", "name", "status", "objective",
        "created_time", "updated_time",
        "daily_budget", "lifetime_budget",
        "budget_remaining", "spend_cap",
        "start_time", "stop_time",
        "buying_type", "bid_strategy",
        "special_ad_categories"
    ]
}

# Default limits for different contexts
DEFAULT_LIMITS = {
    "claude_desktop": 25,  # Optimized for Claude Desktop
    "claude_code": 100,    # Claude Code can handle more
    "api_max": 500         # Meta API maximum
}

# Default time ranges
DEFAULT_TIME_RANGES = {
    "quick_check": "last_7d",
    "standard": "last_30d",
    "detailed": "last_90d"
}


def get_insight_fields(preset: str = "efficiency") -> str:
    """
    Get insight fields for a preset.

    Args:
        preset: Preset name (basic, efficiency, conversions, video, full)

    Returns:
        Comma-separated field string
    """
    fields = INSIGHT_PRESETS.get(preset, INSIGHT_PRESETS["efficiency"])
    return ",".join(fields)


def get_campaign_fields(preset: str = "basic") -> str:
    """
    Get campaign fields for a preset.

    Args:
        preset: Preset name (basic, full)

    Returns:
        Comma-separated field string
    """
    fields = CAMPAIGN_PRESETS.get(preset, CAMPAIGN_PRESETS["basic"])
    return ",".join(fields)


def get_default_limit(context: str = "claude_desktop") -> int:
    """
    Get default limit for context.

    Args:
        context: Usage context (claude_desktop, claude_code, api_max)

    Returns:
        Appropriate limit value
    """
    return DEFAULT_LIMITS.get(context, DEFAULT_LIMITS["claude_desktop"])
```

**Verification:**
```bash
python -c "from meta_ads_mcp.core.presets import get_insight_fields; print(get_insight_fields('basic'))"
```

---

#### Step 2.3.2: Update get_insights with presets

**Action:** Add field_preset parameter to get_insights

**Location:** `meta-ads-mcp/meta_ads_mcp/core/insights.py`

**Implementation:**

Update the function signature and add preset handling:

```python
from .presets import get_insight_fields, get_default_limit

@mcp_server.tool()
@meta_api_tool
async def get_insights(
    object_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",  # Changed default
    breakdown: str = "",
    level: str = "ad",
    limit: int = 25,  # Changed default from 100
    after: str = "",
    field_preset: str = "",  # NEW: basic, efficiency, conversions, video, full
    fields: Optional[List[str]] = None,
    # ... existing parameters ...
) -> str:
    """
    Get performance insights with optional field presets.

    Args:
        object_id: ID of campaign, ad set, ad, or account
        time_range: Time period (default: last_30d)
        limit: Results per page (default: 25 for Claude Desktop)
        field_preset: Use preset fields (basic, efficiency, conversions, video, full)
        fields: Custom field list (overrides preset)
        ...
    """
    # Handle field preset
    if field_preset and not fields:
        fields_str = get_insight_fields(field_preset)
    elif fields:
        fields_str = ",".join(fields)
    else:
        # Use efficiency preset as default
        fields_str = get_insight_fields("efficiency")

    # ... rest of implementation using fields_str ...
```

**Verification:**
```bash
# Test with Claude: "Get insights for campaign 123 with video preset"
```

---

### 2.4 Get Capabilities Tool

**Why it matters:** Self-documenting API. Users can discover available tools and their parameters without external documentation.

**Prerequisites:**
- None

**Complexity:** 1 step

**Dependencies:** None

---

#### Step 2.4.1: Create get_capabilities tool

**Action:** Add tool that lists all available MCP tools and presets

**Location:** `meta-ads-mcp/meta_ads_mcp/core/server.py`

**Implementation:**

Add at the end of the server module:

```python
@mcp_server.tool()
async def get_capabilities() -> str:
    """
    Get list of all available Meta Ads MCP tools and capabilities.

    Returns comprehensive info about:
    - All available tools with descriptions
    - Field presets for insights
    - Default time ranges
    - API version info
    """
    from .presets import INSIGHT_PRESETS, DEFAULT_TIME_RANGES, DEFAULT_LIMITS
    from .api import API_VERSION

    # Get all registered tools
    tools = []
    for tool in mcp_server.list_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description[:100] + "..." if len(tool.description) > 100 else tool.description
        })

    return json.dumps({
        "meta_ads_mcp": {
            "version": "1.0.0",
            "api_version": API_VERSION,
            "tool_count": len(tools)
        },
        "tools": tools,
        "insight_presets": {
            name: fields for name, fields in INSIGHT_PRESETS.items()
        },
        "time_range_presets": list(DEFAULT_TIME_RANGES.keys()),
        "default_limits": DEFAULT_LIMITS,
        "common_workflows": [
            "1. health_check - Verify API connectivity",
            "2. get_ad_accounts - List accessible accounts",
            "3. get_campaigns - List campaigns for account",
            "4. get_insights - Get performance metrics",
            "5. compare_entities - Compare A/B performance"
        ]
    }, indent=2)
```

**Verification:**
```bash
# Test with Claude: "What tools are available?"
```

---

## Priority Tier 3: Nice-to-Have

### 3.1 Export to CSV/JSON

**Why it matters:** Enables data export for external analysis or reporting. Situational but useful for data handoffs.

**Prerequisites:**
- get_insights working

**Complexity:** 1 step

**Dependencies:** None

---

#### Step 3.1.1: Create export_insights tool

**Action:** Add tool to export insights in CSV or JSON format

**Location:** `meta-ads-mcp/meta_ads_mcp/core/insights.py`

**Implementation:**
```python
import csv
import io

@mcp_server.tool()
@meta_api_tool
async def export_insights(
    object_id: str,
    format: str = "json",
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "ad",
    field_preset: str = "efficiency",
    limit: int = 100,
    access_token: Optional[str] = None
) -> str:
    """
    Export insights data in CSV or JSON format.

    Args:
        object_id: Account, campaign, ad set, or ad ID
        format: Output format - "json" or "csv" (default: json)
        time_range: Time period (default: last_30d)
        level: Aggregation level (default: ad)
        field_preset: Field preset to use (default: efficiency)
        limit: Maximum rows (default: 100)

    Returns:
        Formatted data string (CSV or JSON)

    Note:
        CSV format is more compact but loses nested structure.
        Use JSON for programmatic processing.
    """
    # Get insights data
    result = await get_insights(
        object_id=object_id,
        time_range=time_range,
        level=level,
        field_preset=field_preset,
        limit=limit,
        access_token=access_token
    )

    data = json.loads(result)

    if "error" in data:
        return result

    if format.lower() == "csv":
        # Convert to CSV
        if not data.get("data"):
            return "No data to export"

        output = io.StringIO()
        rows = data["data"]

        # Get all unique keys across all rows
        all_keys = set()
        for row in rows:
            all_keys.update(row.keys())

        # Filter out complex nested objects for CSV
        simple_keys = [k for k in all_keys if not isinstance(rows[0].get(k), (dict, list))]
        simple_keys.sort()

        writer = csv.DictWriter(output, fieldnames=simple_keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

        csv_content = output.getvalue()
        return f"# Exported {len(rows)} rows\n# Time range: {time_range}\n\n{csv_content}"

    else:
        # Return formatted JSON
        return json.dumps({
            "export": {
                "format": "json",
                "time_range": time_range,
                "level": level,
                "row_count": len(data.get("data", []))
            },
            "data": data.get("data", [])
        }, indent=2)
```

**Verification:**
```bash
# Test with Claude: "Export insights for account act_XXX as CSV"
```

---

### 3.2 Creative Validation Helpers

**Why it matters:** Pre-validates creative content before submission. Situational because Meta validates on submit anyway.

**Prerequisites:**
- Creative tools working

**Complexity:** 1 step

**Dependencies:** None

---

#### Step 3.2.1: Create validate_creative tool

**Action:** Add tool to validate creative specifications before submission

**Location:** `meta-ads-mcp/meta_ads_mcp/core/ads.py`

**Implementation:**
```python
@mcp_server.tool()
async def validate_creative_specs(
    headline: Optional[str] = None,
    primary_text: Optional[str] = None,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    call_to_action: Optional[str] = None
) -> str:
    """
    Validate creative specifications against Meta best practices.

    Checks:
    - Character limits for text fields
    - Valid call-to-action types
    - Image URL accessibility (if provided)

    Args:
        headline: Ad headline text
        primary_text: Main ad copy
        description: Link description
        image_url: URL to ad image
        call_to_action: CTA button type

    Returns:
        JSON with validation results and recommendations
    """
    issues = []
    warnings = []
    recommendations = []

    # Character limit checks (Meta guidelines)
    LIMITS = {
        "headline": {"max": 40, "recommended": 25},
        "primary_text": {"max": 125, "recommended": 80},
        "description": {"max": 30, "recommended": 20}
    }

    if headline:
        if len(headline) > LIMITS["headline"]["max"]:
            issues.append(f"Headline exceeds {LIMITS['headline']['max']} chars (has {len(headline)})")
        elif len(headline) > LIMITS["headline"]["recommended"]:
            warnings.append(f"Headline over {LIMITS['headline']['recommended']} chars may be truncated on mobile")

    if primary_text:
        if len(primary_text) > LIMITS["primary_text"]["max"]:
            warnings.append(f"Primary text over {LIMITS['primary_text']['max']} chars will be truncated")
        elif len(primary_text) > LIMITS["primary_text"]["recommended"]:
            recommendations.append("Consider shorter primary text for better engagement")

    if description:
        if len(description) > LIMITS["description"]["max"]:
            issues.append(f"Description exceeds {LIMITS['description']['max']} chars")

    # CTA validation
    VALID_CTAS = [
        "BOOK_TRAVEL", "CONTACT_US", "DOWNLOAD", "GET_OFFER",
        "GET_QUOTE", "LEARN_MORE", "LISTEN_NOW", "MESSAGE_PAGE",
        "NO_BUTTON", "OPEN_LINK", "ORDER_NOW", "PLAY_GAME",
        "SHOP_NOW", "SIGN_UP", "SUBSCRIBE", "WATCH_MORE"
    ]

    if call_to_action:
        if call_to_action.upper() not in VALID_CTAS:
            issues.append(f"Invalid CTA '{call_to_action}'. Valid: {', '.join(VALID_CTAS[:5])}...")

    # Image URL check
    if image_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(image_url, timeout=5) as response:
                    if response.status != 200:
                        issues.append(f"Image URL returned status {response.status}")
                    content_type = response.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        warnings.append(f"URL content-type is '{content_type}', expected image/*")
        except Exception as e:
            issues.append(f"Could not verify image URL: {str(e)}")

    # Determine overall status
    if issues:
        status = "invalid"
    elif warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return json.dumps({
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "recommendations": recommendations,
        "character_counts": {
            "headline": len(headline) if headline else 0,
            "primary_text": len(primary_text) if primary_text else 0,
            "description": len(description) if description else 0
        },
        "limits": LIMITS
    }, indent=2)
```

**Verification:**
```bash
# Test with Claude: "Validate creative with headline 'Summer Sale 50% Off' and primary text '...'"
```

**Audit Fix Sub-steps:**
- Use `httpx` with timeouts for image URL checks.
- If `HEAD` fails or returns 405, fall back to `GET` or return a warning.

---

## Implementation Checklist

### Tier 1: Essential (Do First)
- [ ] 1.1 Centralized Retry/Backoff
  - [ ] 1.1.1 Create retry.py module
  - [ ] 1.1.2 Add to core exports
  - [ ] 1.1.3 Integrate into API client
  - [ ] 1.1.4 Add unit tests
- [ ] 1.2 Health Check Tool
  - [ ] 1.2.1 Create health_check function
  - [ ] 1.2.2 Add test
- [ ] 1.3 API v23.0 Upgrade
  - [ ] 1.3.1 Create version configuration
  - [ ] 1.3.2 Update hardcoded URLs
  - [ ] 1.3.3 Document configuration
- [ ] 1.4 Pagination Helpers
  - [ ] 1.4.1 Create pagination.py module
  - [ ] 1.4.2 Add fetch_all to list tools
  - [ ] 1.4.3 Add tests

### Tier 2: High Value (Do Second)
- [ ] 2.1 Token Validation Tools
  - [ ] 2.1.1 Create get_token_info and validate_token
- [ ] 2.2 Compare Entities Helper
  - [ ] 2.2.1 Create compare_entities tool
- [ ] 2.3 Default Limits & Presets
  - [ ] 2.3.1 Create presets.py module
  - [ ] 2.3.2 Update get_insights with presets
- [ ] 2.4 Get Capabilities Tool
  - [ ] 2.4.1 Create get_capabilities tool

### Tier 3: Nice-to-Have (Do If Time)
- [x] 3.1 Export to CSV/JSON
  - [x] 3.1.1 Create export_insights tool
- [x] 3.2 Creative Validation Helpers
  - [x] 3.2.1 Create validate_creative_specs tool

---

## Step Summary

| Tier | Improvements | Steps | Sub-steps |
|------|--------------|-------|-----------|
| Tier 1: Essential | 4 | 12 | 12 |
| Tier 2: High Value | 4 | 5 | 5 |
| Tier 3: Nice-to-Have | 2 | 2 | 2 |
| **Total** | **10** | **19** | **19** |

### Breakdown by Improvement

| # | Improvement | Steps |
|---|-------------|-------|
| 1.1 | Centralized Retry/Backoff | 4 (create module, exports, integrate, tests) |
| 1.2 | Health Check Tool | 2 (create tool, add test) |
| 1.3 | API v23.0 Upgrade | 3 (config, update URLs, document) |
| 1.4 | Pagination Helpers | 3 (create module, add fetch_all, tests) |
| 2.1 | Token Validation Tools | 1 (create get_token_info + validate_token) |
| 2.2 | Compare Entities Helper | 1 (create compare_entities) |
| 2.3 | Default Limits & Presets | 2 (create presets, update get_insights) |
| 2.4 | Get Capabilities Tool | 1 (create get_capabilities) |
| 3.1 | Export to CSV/JSON | 1 (create export_insights) |
| 3.2 | Creative Validation | 1 (create validate_creative_specs) |

---

## Notes

- All code examples assume the existing project structure
- Test after each step before proceeding
- Restart MCP server after making changes to test with Claude
- Commit after each completed improvement for easy rollback

---
## Audit Findings (2026-01-09)

### Issues Requiring Action
- Step 1.1.1 (Correctness/Completeness): `with_retry` ignores decorator `max_retries` and `parse_meta_error` cannot honor `Retry-After` headers. Fix by capping retries with `min(max_retries, e.max_retries)` and passing response headers into `parse_meta_error`.
- Step 1.1.3 (Correctness/Completeness): Retry integration only handles JSON `"error"` responses; no retry on non-JSON or transport errors. Wrap the actual HTTP call, raise on retryable HTTP status codes, and handle timeouts/network exceptions.
- Step 1.2.1 (Correctness/Feasibility): Uses `aiohttp`, hardcodes `v22.0`, and uses a user token for `debug_token`. Switch to `httpx`, use `get_api_base_url()`, and use app access token for `debug_token`.
- Step 1.4.1 (Correctness/Feasibility): Pagination helper uses `aiohttp` and bypasses shared retry/auth. Implement with `httpx` and/or `make_api_request` plus timeouts.
- Step 1.4.2 (Completeness/Clarity): `url` not defined; access token handling and pagination metadata missing. Add explicit URL construction, token resolution, and return `pagination_info`.
- Step 1.4.3 (Completeness): Tests only cover `add_pagination_params`. Add tests for `fetch_all_pages`/`paginate_generator` with mocked responses.
- Step 2.1.1 (Correctness/Feasibility): Uses `aiohttp` and undefined `API_VERSION`, and uses user token for `debug_token`. Import `get_api_base_url`/`get_api_version`, use `httpx`, and use app access token.
- Step 3.2.1 (Feasibility/Completeness): Uses `aiohttp` without guidance and no fallback if `HEAD` fails. Use `httpx` with timeouts and fallback to `GET` or warn.

### Items Flagged for Review
- Step 1.2.2: Clarify whether the health check test is unit (mocked) or e2e (requires real credentials). Current plan is ambiguous.

### Verification Notes
Verified steps: 1.1.2, 1.1.4, 1.3.1, 1.3.2, 1.3.3, 2.2.1, 2.3.1, 2.3.2, 2.4.1, 3.1.1.
