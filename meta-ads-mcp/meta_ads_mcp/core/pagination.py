"""
Pagination helpers for Meta API responses.

Provides utilities for:
- Fetching all pages automatically
- Configurable page limits
- Generator-based iteration for memory efficiency
"""

import httpx
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any

from .api import META_GRAPH_API_BASE

logger = logging.getLogger(__name__)


class PaginationConfig:
    """Configuration for pagination behavior."""

    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100
    MAX_PAGES = 100  # Safety limit
    MAX_ITEMS = 10000  # Safety limit
    REQUEST_TIMEOUT = 30.0


async def fetch_all_pages(
    endpoint: str,
    params: Dict[str, Any],
    access_token: str,
    max_pages: int = PaginationConfig.MAX_PAGES,
    max_items: int = PaginationConfig.MAX_ITEMS,
    data_key: str = "data"
) -> Dict[str, Any]:
    """
    Fetch all pages from a paginated Meta API endpoint.

    Args:
        endpoint: API endpoint path (e.g., "act_123/campaigns")
        params: Query parameters (should include 'fields')
        access_token: Meta API access token
        max_pages: Maximum number of pages to fetch (default: 100)
        max_items: Maximum total items to fetch (default: 10000)
        data_key: Key in response containing data array (default: "data")

    Returns:
        Dict with 'data' containing all items and 'pagination_info' with stats

    Example:
        result = await fetch_all_pages(
            "act_123/campaigns",
            {"fields": "id,name,status"},
            access_token,
            max_pages=10
        )
    """
    all_items: List[Dict] = []
    current_url = f"{META_GRAPH_API_BASE}/{endpoint}"
    current_params = {**params, "access_token": access_token}
    pages_fetched = 0
    has_more = True

    async with httpx.AsyncClient(timeout=PaginationConfig.REQUEST_TIMEOUT) as client:
        while has_more and pages_fetched < max_pages and len(all_items) < max_items:
            try:
                response = await client.get(current_url, params=current_params)
                data = response.json()

                if "error" in data:
                    logger.error(f"Pagination error: {data['error']}")
                    return {
                        "data": all_items,
                        "error": data["error"],
                        "pagination_info": {
                            "pages_fetched": pages_fetched,
                            "total_items": len(all_items),
                            "complete": False,
                            "error_on_page": pages_fetched + 1
                        }
                    }

                # Extract items from response
                items = data.get(data_key, [])
                all_items.extend(items)
                pages_fetched += 1

                logger.debug(
                    f"Fetched page {pages_fetched}: {len(items)} items "
                    f"(total: {len(all_items)})"
                )

                # Check for next page using cursor (not Meta's next URL which has embedded token)
                paging = data.get("paging", {})
                cursors = paging.get("cursors", {})
                after_cursor = cursors.get("after")
                next_url = paging.get("next")

                if after_cursor:
                    # Use cursor directly - preferred method
                    current_params["after"] = after_cursor
                elif next_url:
                    # Fallback: extract after param from next URL
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(next_url)
                    query_params = parse_qs(parsed.query)
                    if "after" in query_params:
                        current_params["after"] = query_params["after"][0]
                    else:
                        has_more = False
                else:
                    has_more = False

            except httpx.TimeoutException:
                logger.error(f"Pagination timeout on page {pages_fetched + 1}")
                return {
                    "data": all_items,
                    "error": {"message": "Request timeout during pagination"},
                    "pagination_info": {
                        "pages_fetched": pages_fetched,
                        "total_items": len(all_items),
                        "complete": False,
                        "error_on_page": pages_fetched + 1
                    }
                }
            except Exception as e:
                logger.error(f"Pagination fetch error: {e}")
                return {
                    "data": all_items,
                    "error": {"message": str(e)},
                    "pagination_info": {
                        "pages_fetched": pages_fetched,
                        "total_items": len(all_items),
                        "complete": False,
                        "error_on_page": pages_fetched + 1
                    }
                }

    # Determine if we hit a limit
    hit_page_limit = pages_fetched >= max_pages
    hit_item_limit = len(all_items) >= max_items

    logger.info(f"Pagination complete: {len(all_items)} items from {pages_fetched} pages")

    return {
        "data": all_items,
        "pagination_info": {
            "pages_fetched": pages_fetched,
            "total_items": len(all_items),
            "complete": not has_more and not hit_page_limit and not hit_item_limit,
            "hit_page_limit": hit_page_limit,
            "hit_item_limit": hit_item_limit,
            "max_pages": max_pages,
            "max_items": max_items
        }
    }


async def paginate_generator(
    endpoint: str,
    params: Dict[str, Any],
    access_token: str,
    max_pages: int = PaginationConfig.MAX_PAGES,
    data_key: str = "data"
) -> AsyncGenerator[Dict, None]:
    """
    Generator-based pagination for memory-efficient iteration.

    Yields items one at a time instead of loading all into memory.

    Args:
        endpoint: API endpoint path (e.g., "act_123/campaigns")
        params: Query parameters
        access_token: Meta API access token
        max_pages: Maximum pages to fetch
        data_key: Key containing data array

    Yields:
        Individual items from each page

    Example:
        async for campaign in paginate_generator("act_123/campaigns", params, token):
            process(campaign)
    """
    current_url = f"{META_GRAPH_API_BASE}/{endpoint}"
    current_params = {**params, "access_token": access_token}
    pages_fetched = 0

    async with httpx.AsyncClient(timeout=PaginationConfig.REQUEST_TIMEOUT) as client:
        while current_url and pages_fetched < max_pages:
            try:
                response = await client.get(current_url, params=current_params)
                data = response.json()

                if "error" in data:
                    logger.error(f"Pagination error: {data['error']}")
                    return

                # Yield items one at a time
                for item in data.get(data_key, []):
                    yield item

                pages_fetched += 1

                # Get next page cursor (not Meta's next URL which has embedded token)
                paging = data.get("paging", {})
                cursors = paging.get("cursors", {})
                after_cursor = cursors.get("after")
                next_url = paging.get("next")

                if after_cursor:
                    # Use cursor directly - preferred method
                    current_params["after"] = after_cursor
                elif next_url:
                    # Fallback: extract after param from next URL
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(next_url)
                    query_params = parse_qs(parsed.query)
                    if "after" in query_params:
                        current_params["after"] = query_params["after"][0]
                    else:
                        return
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


def extract_cursor_from_response(response_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract the 'after' cursor from a paginated response.

    Args:
        response_data: API response containing paging info

    Returns:
        After cursor string if available, None otherwise
    """
    paging = response_data.get("paging", {})
    cursors = paging.get("cursors", {})
    return cursors.get("after")


def has_next_page(response_data: Dict[str, Any]) -> bool:
    """
    Check if there are more pages available.

    Args:
        response_data: API response containing paging info

    Returns:
        True if more pages are available
    """
    paging = response_data.get("paging", {})
    return "next" in paging
