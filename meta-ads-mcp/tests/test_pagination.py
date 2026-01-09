"""Tests for pagination helpers."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from meta_ads_mcp.core.pagination import (
    PaginationConfig,
    fetch_all_pages,
    paginate_generator,
    add_pagination_params,
    extract_cursor_from_response,
    has_next_page,
)


class TestPaginationConfig:
    """Tests for PaginationConfig defaults."""

    def test_default_page_size(self):
        assert PaginationConfig.DEFAULT_PAGE_SIZE == 25

    def test_max_page_size(self):
        assert PaginationConfig.MAX_PAGE_SIZE == 100

    def test_max_pages(self):
        assert PaginationConfig.MAX_PAGES == 100

    def test_max_items(self):
        assert PaginationConfig.MAX_ITEMS == 10000

    def test_request_timeout(self):
        assert PaginationConfig.REQUEST_TIMEOUT == 30.0


class TestAddPaginationParams:
    """Tests for add_pagination_params helper."""

    def test_adds_default_limit(self):
        params = {"fields": "id,name"}
        result = add_pagination_params(params)
        assert result["limit"] == PaginationConfig.DEFAULT_PAGE_SIZE
        assert result["fields"] == "id,name"

    def test_adds_custom_limit(self):
        params = {"fields": "id,name"}
        result = add_pagination_params(params, limit=50)
        assert result["limit"] == 50

    def test_caps_limit_at_max(self):
        params = {}
        result = add_pagination_params(params, limit=200)
        assert result["limit"] == PaginationConfig.MAX_PAGE_SIZE

    def test_adds_after_cursor(self):
        params = {"fields": "id"}
        result = add_pagination_params(params, after="cursor123")
        assert result["after"] == "cursor123"

    def test_no_after_when_none(self):
        params = {"fields": "id"}
        result = add_pagination_params(params, after=None)
        assert "after" not in result

    def test_preserves_existing_params(self):
        params = {"fields": "id,name", "status": "ACTIVE"}
        result = add_pagination_params(params, limit=10)
        assert result["fields"] == "id,name"
        assert result["status"] == "ACTIVE"
        assert result["limit"] == 10


class TestExtractCursorFromResponse:
    """Tests for extract_cursor_from_response helper."""

    def test_extracts_cursor(self):
        response = {
            "data": [],
            "paging": {
                "cursors": {
                    "before": "before123",
                    "after": "after456"
                }
            }
        }
        assert extract_cursor_from_response(response) == "after456"

    def test_returns_none_when_no_paging(self):
        response = {"data": []}
        assert extract_cursor_from_response(response) is None

    def test_returns_none_when_no_cursors(self):
        response = {"data": [], "paging": {}}
        assert extract_cursor_from_response(response) is None

    def test_returns_none_when_no_after(self):
        response = {
            "data": [],
            "paging": {"cursors": {"before": "before123"}}
        }
        assert extract_cursor_from_response(response) is None


class TestHasNextPage:
    """Tests for has_next_page helper."""

    def test_returns_true_when_next_exists(self):
        response = {
            "data": [],
            "paging": {"next": "https://graph.facebook.com/v23.0/..."}
        }
        assert has_next_page(response) is True

    def test_returns_false_when_no_next(self):
        response = {
            "data": [],
            "paging": {"previous": "https://..."}
        }
        assert has_next_page(response) is False

    def test_returns_false_when_no_paging(self):
        response = {"data": []}
        assert has_next_page(response) is False


class TestFetchAllPages:
    """Tests for fetch_all_pages function."""

    @pytest.mark.asyncio
    async def test_fetches_single_page(self):
        """Test fetching when only one page exists."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert len(result["data"]) == 2
        assert result["pagination_info"]["pages_fetched"] == 1
        assert result["pagination_info"]["complete"] is True

    @pytest.mark.asyncio
    async def test_fetches_multiple_pages(self):
        """Test fetching multiple pages."""
        page1_response = MagicMock()
        page1_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        page2_response = MagicMock()
        page2_response.json.return_value = {
            "data": [{"id": "2"}],
            "paging": {}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [page1_response, page2_response]
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert len(result["data"]) == 2
        assert result["pagination_info"]["pages_fetched"] == 2
        assert result["pagination_info"]["complete"] is True

    @pytest.mark.asyncio
    async def test_respects_max_pages_limit(self):
        """Test that max_pages limit is respected."""
        page_response = MagicMock()
        page_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = page_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token",
                max_pages=3
            )

        assert result["pagination_info"]["pages_fetched"] == 3
        assert result["pagination_info"]["hit_page_limit"] is True
        assert result["pagination_info"]["complete"] is False

    @pytest.mark.asyncio
    async def test_respects_max_items_limit(self):
        """Test that max_items limit is respected."""
        page_response = MagicMock()
        page_response.json.return_value = {
            "data": [{"id": str(i)} for i in range(100)],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = page_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token",
                max_items=150
            )

        assert len(result["data"]) >= 150
        assert result["pagination_info"]["hit_item_limit"] is True

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"message": "Invalid token", "code": 190}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert "error" in result
        assert result["error"]["code"] == 190
        assert result["pagination_info"]["complete"] is False

    @pytest.mark.asyncio
    async def test_handles_timeout(self):
        """Test handling of timeout errors."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert "error" in result
        assert "timeout" in result["error"]["message"].lower()
        assert result["pagination_info"]["complete"] is False

    @pytest.mark.asyncio
    async def test_handles_generic_exception(self):
        """Test handling of generic exceptions."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert "error" in result
        assert result["pagination_info"]["complete"] is False

    @pytest.mark.asyncio
    async def test_partial_results_on_error(self):
        """Test that partial results are returned on mid-pagination error."""
        page1_response = MagicMock()
        page1_response.json.return_value = {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [
                page1_response,
                httpx.TimeoutException("Timeout")
            ]
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            )

        assert len(result["data"]) == 2
        assert "error" in result
        assert result["pagination_info"]["error_on_page"] == 2


class TestPaginateGenerator:
    """Tests for paginate_generator function."""

    @pytest.mark.asyncio
    async def test_yields_items_from_single_page(self):
        """Test yielding items from a single page."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"id": "1"}, {"id": "2"}],
            "paging": {}
        }

        items = []
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            async for item in paginate_generator(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            ):
                items.append(item)

        assert len(items) == 2
        assert items[0]["id"] == "1"
        assert items[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_yields_items_from_multiple_pages(self):
        """Test yielding items across multiple pages."""
        page1_response = MagicMock()
        page1_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        page2_response = MagicMock()
        page2_response.json.return_value = {
            "data": [{"id": "2"}],
            "paging": {}
        }

        items = []
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [page1_response, page2_response]
            MockClient.return_value.__aenter__.return_value = mock_client

            async for item in paginate_generator(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            ):
                items.append(item)

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_stops_on_max_pages(self):
        """Test generator stops at max_pages."""
        page_response = MagicMock()
        page_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {"next": "https://graph.facebook.com/next"}
        }

        items = []
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = page_response
            MockClient.return_value.__aenter__.return_value = mock_client

            async for item in paginate_generator(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token",
                max_pages=2
            ):
                items.append(item)

        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_stops_on_error(self):
        """Test generator stops gracefully on error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"message": "Error", "code": 100}
        }

        items = []
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            async for item in paginate_generator(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token"
            ):
                items.append(item)

        assert len(items) == 0


class TestPaginationIntegration:
    """Integration-style tests for pagination."""

    @pytest.mark.asyncio
    async def test_pagination_info_format(self):
        """Test that pagination_info has all expected fields."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"id": "1"}],
            "paging": {}
        }

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await fetch_all_pages(
                "act_123/campaigns",
                {"fields": "id"},
                "test_token",
                max_pages=10,
                max_items=100
            )

        info = result["pagination_info"]
        assert "pages_fetched" in info
        assert "total_items" in info
        assert "complete" in info
        assert "hit_page_limit" in info
        assert "hit_item_limit" in info
        assert "max_pages" in info
        assert "max_items" in info
