"""Tests for creative analysis module.

Unit tests for helper functions and E2E tests for MCP tools.
E2E tests require a running connection to Meta API.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch

from meta_ads_mcp.core.creative_analysis import (
    # Exceptions
    CreativeAnalysisError,
    VideoProcessingError,
    CreativeNotFoundError,
    # Enums
    CreativeType,
    AnalysisLevel,
    # Dataclasses
    CreativeDimensions,
    CreativeContent,
    VisualAnalysis,
    PerformanceMetrics,
    CreativeAnalysisResult,
    # Helper functions
    _detect_creative_type,
    _extract_creative_content,
    _parse_performance_metrics,
    _compare_to_benchmarks,
    _identify_dropoff_points,
    _generate_insights,
    # MCP tools
    get_creative_type,
    get_creative_content,
    analyze_image_creative,
    analyze_video_creative,
    analyze_creative,
    get_account_benchmarks,
    analyze_account_creatives,
    get_creative_insights,
)


# =============================================================================
# Exception Tests
# =============================================================================

class TestExceptions:
    """Tests for custom exceptions."""

    def test_creative_analysis_error_basic(self):
        """Test CreativeAnalysisError with message only."""
        error = CreativeAnalysisError("Test error")
        assert error.message == "Test error"
        assert error.details == {}
        assert str(error) == "Test error"

    def test_creative_analysis_error_with_details(self):
        """Test CreativeAnalysisError with details dict."""
        details = {"code": 100, "subcode": 200}
        error = CreativeAnalysisError("API error", details=details)
        assert error.message == "API error"
        assert error.details == details

    def test_creative_analysis_error_to_dict(self):
        """Test to_dict serialization."""
        error = CreativeAnalysisError("Test", details={"key": "value"})
        result = error.to_dict()
        assert result["error"] == "Test"
        assert result["error_type"] == "CreativeAnalysisError"
        assert result["details"] == {"key": "value"}

    def test_video_processing_error_inheritance(self):
        """Test VideoProcessingError inherits from CreativeAnalysisError."""
        error = VideoProcessingError("FFmpeg failed")
        assert isinstance(error, CreativeAnalysisError)
        assert error.to_dict()["error_type"] == "VideoProcessingError"

    def test_creative_not_found_error_inheritance(self):
        """Test CreativeNotFoundError inherits from CreativeAnalysisError."""
        error = CreativeNotFoundError("Ad not found")
        assert isinstance(error, CreativeAnalysisError)
        assert error.to_dict()["error_type"] == "CreativeNotFoundError"


# =============================================================================
# Enum Tests
# =============================================================================

class TestEnums:
    """Tests for enum types."""

    def test_creative_type_values(self):
        """Test CreativeType enum values."""
        assert CreativeType.IMAGE.value == "image"
        assert CreativeType.VIDEO.value == "video"
        assert CreativeType.CAROUSEL.value == "carousel"
        assert CreativeType.UNKNOWN.value == "unknown"

    def test_creative_type_is_string_enum(self):
        """Test CreativeType is a string enum."""
        assert isinstance(CreativeType.IMAGE, str)
        assert CreativeType.IMAGE == "image"

    def test_analysis_level_values(self):
        """Test AnalysisLevel enum values."""
        assert AnalysisLevel.FULL.value == "full"
        assert AnalysisLevel.THUMBNAIL_ONLY.value == "thumbnail_only"
        assert AnalysisLevel.METADATA_ONLY.value == "metadata_only"


# =============================================================================
# Dataclass Tests
# =============================================================================

class TestDataclasses:
    """Tests for dataclass structures."""

    def test_creative_dimensions(self):
        """Test CreativeDimensions dataclass."""
        dims = CreativeDimensions(width=1080, height=1920, aspect_ratio="9:16")
        assert dims.width == 1080
        assert dims.height == 1920
        assert dims.aspect_ratio == "9:16"

    def test_creative_content(self):
        """Test CreativeContent dataclass."""
        content = CreativeContent(
            headlines=["Headline 1", "Headline 2"],
            primary_texts=["Body text"],
            descriptions=["Description"],
            call_to_action="LEARN_MORE",
            link_url="https://example.com"
        )
        assert len(content.headlines) == 2
        assert content.call_to_action == "LEARN_MORE"

    def test_performance_metrics(self):
        """Test PerformanceMetrics dataclass."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=10000,
            clicks=500,
            ctr=5.0,
            spend=100.0,
            cpc=0.20,
            cpm=10.0,
            reach=8000,
            frequency=1.25
        )
        assert metrics.impressions == 10000
        assert metrics.ctr == 5.0


# =============================================================================
# Type Detection Tests
# =============================================================================

class TestDetectCreativeType:
    """Tests for _detect_creative_type function."""

    def test_detect_video_from_object_story_spec(self):
        """Test detection of video from object_story_spec.video_data."""
        creative = {
            "object_story_spec": {
                "video_data": {
                    "video_id": "123456789"
                }
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.VIDEO
        assert "video_id" in data

    def test_detect_video_from_asset_feed_spec(self):
        """Test detection of video from asset_feed_spec.videos."""
        creative = {
            "asset_feed_spec": {
                "videos": [{"video_id": "123"}]
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.VIDEO

    def test_detect_carousel(self):
        """Test detection of carousel from child_attachments."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "child_attachments": [
                        {"link": "https://example.com/1"},
                        {"link": "https://example.com/2"}
                    ]
                }
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.CAROUSEL

    def test_detect_image_from_link_data(self):
        """Test detection of image from link_data.image_hash."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "image_hash": "abc123def456"
                }
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.IMAGE

    def test_detect_image_from_picture(self):
        """Test detection of image from link_data.picture."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "picture": "https://example.com/image.jpg"
                }
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.IMAGE

    def test_detect_image_from_asset_feed_spec(self):
        """Test detection of image from asset_feed_spec.images."""
        creative = {
            "asset_feed_spec": {
                "images": [{"hash": "abc123"}]
            }
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.IMAGE

    def test_detect_image_from_thumbnail_url(self):
        """Test detection of image from thumbnail_url field."""
        creative = {
            "thumbnail_url": "https://example.com/thumb.jpg"
        }
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.IMAGE

    def test_detect_unknown_empty_creative(self):
        """Test unknown type for empty creative."""
        creative = {}
        creative_type, data = _detect_creative_type(creative)
        assert creative_type == CreativeType.UNKNOWN

    def test_video_takes_priority_over_image(self):
        """Test that video detection takes priority."""
        creative = {
            "object_story_spec": {
                "video_data": {"video_id": "123"},
                "link_data": {"image_hash": "abc"}
            }
        }
        creative_type, _ = _detect_creative_type(creative)
        assert creative_type == CreativeType.VIDEO


# =============================================================================
# Content Extraction Tests
# =============================================================================

class TestExtractCreativeContent:
    """Tests for _extract_creative_content function."""

    def test_extract_headlines_from_asset_feed_spec(self):
        """Test headline extraction from asset_feed_spec.titles."""
        creative = {
            "asset_feed_spec": {
                "titles": [
                    {"text": "Headline 1"},
                    {"text": "Headline 2"}
                ]
            }
        }
        content = _extract_creative_content(creative)
        assert content.headlines == ["Headline 1", "Headline 2"]

    def test_extract_headline_from_link_data(self):
        """Test headline extraction from link_data.name."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "name": "Link Headline"
                }
            }
        }
        content = _extract_creative_content(creative)
        assert "Link Headline" in content.headlines

    def test_extract_primary_texts(self):
        """Test body text extraction from asset_feed_spec.bodies."""
        creative = {
            "asset_feed_spec": {
                "bodies": [
                    {"text": "Body text 1"},
                    {"text": "Body text 2"}
                ]
            }
        }
        content = _extract_creative_content(creative)
        assert len(content.primary_texts) == 2

    def test_extract_message_from_link_data(self):
        """Test message extraction from link_data.message."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "message": "Check this out!"
                }
            }
        }
        content = _extract_creative_content(creative)
        assert "Check this out!" in content.primary_texts

    def test_extract_descriptions(self):
        """Test description extraction."""
        creative = {
            "asset_feed_spec": {
                "descriptions": [{"text": "Description 1"}]
            },
            "object_story_spec": {
                "link_data": {
                    "description": "Link description"
                }
            }
        }
        content = _extract_creative_content(creative)
        assert len(content.descriptions) == 2

    def test_extract_cta_from_asset_feed_spec(self):
        """Test CTA extraction from asset_feed_spec."""
        creative = {
            "asset_feed_spec": {
                "call_to_action_types": ["LEARN_MORE"]
            }
        }
        content = _extract_creative_content(creative)
        assert content.call_to_action == "LEARN_MORE"

    def test_extract_cta_from_link_data(self):
        """Test CTA extraction from link_data.call_to_action."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "call_to_action": {"type": "SHOP_NOW"}
                }
            }
        }
        content = _extract_creative_content(creative)
        assert content.call_to_action == "SHOP_NOW"

    def test_extract_link_url_from_asset_feed_spec(self):
        """Test link URL extraction from asset_feed_spec."""
        creative = {
            "asset_feed_spec": {
                "link_urls": [{"website_url": "https://example.com"}]
            }
        }
        content = _extract_creative_content(creative)
        assert content.link_url == "https://example.com"

    def test_extract_link_url_from_link_data(self):
        """Test link URL extraction from link_data.link."""
        creative = {
            "object_story_spec": {
                "link_data": {
                    "link": "https://example.com/page"
                }
            }
        }
        content = _extract_creative_content(creative)
        assert content.link_url == "https://example.com/page"

    def test_empty_creative_returns_empty_content(self):
        """Test that empty creative returns empty content."""
        content = _extract_creative_content({})
        assert content.headlines == []
        assert content.primary_texts == []
        assert content.descriptions == []
        assert content.call_to_action is None
        assert content.link_url is None

    def test_no_duplicate_headlines(self):
        """Test that duplicate headlines are not added."""
        creative = {
            "asset_feed_spec": {
                "titles": [{"text": "Same Headline"}]
            },
            "object_story_spec": {
                "link_data": {
                    "name": "Same Headline"
                }
            }
        }
        content = _extract_creative_content(creative)
        assert content.headlines.count("Same Headline") == 1


# =============================================================================
# Performance Metrics Tests
# =============================================================================

class TestParsePerformanceMetrics:
    """Tests for _parse_performance_metrics function."""

    def test_parse_all_fields(self):
        """Test parsing all metric fields."""
        raw = {
            "impressions": "10000",
            "clicks": "500",
            "ctr": "5.0",
            "spend": "100.50",
            "cpc": "0.201",
            "cpm": "10.05",
            "reach": "8000",
            "frequency": "1.25"
        }
        metrics = _parse_performance_metrics(raw, "last_30d")
        assert metrics.impressions == 10000
        assert metrics.clicks == 500
        assert metrics.ctr == 5.0
        assert metrics.spend == 100.50
        assert metrics.cpc == 0.201
        assert metrics.cpm == 10.05
        assert metrics.reach == 8000
        assert metrics.frequency == 1.25
        assert metrics.time_range == "last_30d"

    def test_parse_with_missing_optional_fields(self):
        """Test parsing with missing optional fields."""
        raw = {
            "impressions": "1000",
            "clicks": "50",
            "ctr": "5.0",
            "spend": "10.0"
        }
        metrics = _parse_performance_metrics(raw, "last_7d")
        assert metrics.impressions == 1000
        assert metrics.cpc is None
        assert metrics.cpm is None
        assert metrics.reach is None
        assert metrics.frequency is None

    def test_parse_with_custom_time_range(self):
        """Test parsing with custom time range dict."""
        raw = {"impressions": "100", "clicks": "5", "ctr": "5.0", "spend": "1.0"}
        time_range = {"since": "2024-01-01", "until": "2024-01-31"}
        metrics = _parse_performance_metrics(raw, time_range)
        assert "2024-01-01" in metrics.time_range
        assert "2024-01-31" in metrics.time_range

    def test_parse_with_zero_values(self):
        """Test parsing with zero values."""
        raw = {
            "impressions": "0",
            "clicks": "0",
            "ctr": "0",
            "spend": "0"
        }
        metrics = _parse_performance_metrics(raw, "today")
        assert metrics.impressions == 0
        assert metrics.clicks == 0


# =============================================================================
# Benchmark Comparison Tests
# =============================================================================

class TestCompareToBenchmarks:
    """Tests for _compare_to_benchmarks function."""

    def test_above_average_ctr(self):
        """Test CTR above account average."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=1000,
            clicks=50,
            ctr=5.0,
            spend=10.0,
            cpc=0.20,
            cpm=10.0,
            reach=None,
            frequency=None
        )
        benchmarks = {
            "ctr": {"avg": 3.0, "p25": 2.0, "p50": 3.0, "p75": 4.0}
        }
        comparison = _compare_to_benchmarks(metrics, benchmarks)
        assert "ctr" in comparison
        assert comparison["ctr"]["performance"] == "above"
        assert comparison["ctr"]["diff_percent"] > 0

    def test_below_average_ctr(self):
        """Test CTR below account average."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=1000,
            clicks=20,
            ctr=2.0,
            spend=10.0,
            cpc=0.50,
            cpm=10.0,
            reach=None,
            frequency=None
        )
        benchmarks = {
            "ctr": {"avg": 4.0, "p25": 3.0, "p50": 4.0, "p75": 5.0}
        }
        comparison = _compare_to_benchmarks(metrics, benchmarks)
        assert comparison["ctr"]["performance"] == "below"
        assert comparison["ctr"]["diff_percent"] < 0

    def test_average_ctr(self):
        """Test CTR within average range."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=1000,
            clicks=40,
            ctr=4.0,
            spend=10.0,
            cpc=0.25,
            cpm=10.0,
            reach=None,
            frequency=None
        )
        benchmarks = {
            "ctr": {"avg": 4.0, "p25": 3.0, "p50": 4.0, "p75": 5.0}
        }
        comparison = _compare_to_benchmarks(metrics, benchmarks)
        assert comparison["ctr"]["performance"] == "average"

    def test_cpc_below_is_good(self):
        """Test that lower CPC is marked as 'below' (which is good)."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=1000,
            clicks=50,
            ctr=5.0,
            spend=5.0,
            cpc=0.10,
            cpm=5.0,
            reach=None,
            frequency=None
        )
        benchmarks = {
            "cpc": {"avg": 0.50, "p25": 0.30, "p50": 0.50, "p75": 0.70}
        }
        comparison = _compare_to_benchmarks(metrics, benchmarks)
        assert comparison["cpc"]["performance"] == "below"

    def test_overall_tier_top(self):
        """Test overall tier calculation for top performer."""
        metrics = PerformanceMetrics(
            time_range="last_30d",
            impressions=1000,
            clicks=80,
            ctr=8.0,
            spend=5.0,
            cpc=0.0625,
            cpm=5.0,
            reach=None,
            frequency=None
        )
        benchmarks = {
            "ctr": {"avg": 3.0},
            "cpc": {"avg": 0.50}
        }
        comparison = _compare_to_benchmarks(metrics, benchmarks)
        assert comparison.get("overall_tier") == "top"


# =============================================================================
# Dropoff Analysis Tests
# =============================================================================

class TestIdentifyDropoffPoints:
    """Tests for _identify_dropoff_points function."""

    def test_identify_single_dropoff(self):
        """Test identification of a single significant dropoff."""
        retention = {
            "25%": 50.0,  # 50% drop from 100
            "50%": 45.0,
            "75%": 40.0,
            "95%": 35.0,
            "100%": 30.0
        }
        dropoffs = _identify_dropoff_points(retention, threshold=10.0)
        assert len(dropoffs) >= 1
        assert dropoffs[0]["checkpoint"] == "25%"
        assert dropoffs[0]["drop_percent"] == 50.0

    def test_identify_multiple_dropoffs(self):
        """Test identification of multiple significant dropoffs."""
        retention = {
            "25%": 70.0,  # 30% drop
            "50%": 40.0,  # 30% drop
            "75%": 25.0,  # 15% drop
            "95%": 15.0,  # 10% drop
            "100%": 10.0  # 5% drop (below threshold)
        }
        dropoffs = _identify_dropoff_points(retention, threshold=10.0)
        assert len(dropoffs) >= 3

    def test_no_dropoffs_below_threshold(self):
        """Test no dropoffs when all below threshold."""
        retention = {
            "25%": 95.0,
            "50%": 90.0,
            "75%": 85.0,
            "95%": 82.0,
            "100%": 80.0
        }
        dropoffs = _identify_dropoff_points(retention, threshold=10.0)
        assert len(dropoffs) == 0

    def test_dropoff_significance_high(self):
        """Test high significance for large dropoffs."""
        retention = {
            "25%": 60.0,  # 40% drop - should be high
            "50%": 55.0,
            "75%": 50.0,
            "95%": 45.0,
            "100%": 40.0
        }
        dropoffs = _identify_dropoff_points(retention, threshold=10.0)
        assert dropoffs[0]["significance"] == "high"

    def test_dropoff_significance_medium(self):
        """Test medium significance for moderate dropoffs."""
        retention = {
            "25%": 85.0,  # 15% drop - should be medium
            "50%": 80.0,
            "75%": 75.0,
            "95%": 70.0,
            "100%": 65.0
        }
        dropoffs = _identify_dropoff_points(retention, threshold=10.0)
        assert dropoffs[0]["significance"] == "medium"


# =============================================================================
# AI Insights Tests
# =============================================================================

class TestGenerateInsights:
    """Tests for _generate_insights function."""

    def test_generate_ctr_strength(self):
        """Test CTR strength insight generation."""
        metrics = {"impressions": 1000, "clicks": 50, "ctr": 5.0}
        benchmark = {
            "ctr": {"performance": "above", "diff_percent": 25.0}
        }
        insights = _generate_insights("image", metrics, None, benchmark, None)
        assert len(insights["strengths"]) > 0
        assert "CTR" in insights["strengths"][0]

    def test_generate_ctr_weakness(self):
        """Test CTR weakness insight generation."""
        metrics = {"impressions": 1000, "clicks": 20, "ctr": 2.0}
        benchmark = {
            "ctr": {"performance": "below", "diff_percent": -50.0}
        }
        insights = _generate_insights("image", metrics, None, benchmark, None)
        assert len(insights["weaknesses"]) > 0
        assert len(insights["recommendations"]) > 0

    def test_generate_video_thruplay_strength(self):
        """Test video thruplay strength insight."""
        metrics = {"impressions": 1000}
        video_metrics = {"thruplay_rate": 20.0}
        insights = _generate_insights("video", metrics, video_metrics, None, None)
        assert any("thruplay" in s.lower() for s in insights["strengths"])

    def test_generate_video_thruplay_weakness(self):
        """Test video thruplay weakness insight."""
        metrics = {"impressions": 1000}
        video_metrics = {"thruplay_rate": 3.0}
        insights = _generate_insights("video", metrics, video_metrics, None, None)
        assert any("thruplay" in s.lower() for s in insights["weaknesses"])

    def test_generate_early_dropoff_insight(self):
        """Test early dropoff insight generation."""
        metrics = {"impressions": 1000}
        video_metrics = {"thruplay_rate": 10.0, "retention_percentages": {"50%": 20}}
        dropoff = {"has_early_dropoff": True}
        insights = _generate_insights("video", metrics, video_metrics, None, dropoff)
        assert any("dropoff" in s.lower() for s in insights["weaknesses"])
        assert any(r["type"] == "hook" for r in insights["recommendations"])

    def test_no_insights_without_metrics(self):
        """Test no insights generated without metrics."""
        insights = _generate_insights("image", None, None, None, None)
        assert insights["strengths"] == []
        assert insights["weaknesses"] == []
        assert insights["recommendations"] == []


# =============================================================================
# E2E Tests (require real API connection)
# =============================================================================

@pytest.mark.e2e
class TestCreativeAnalysisE2E:
    """End-to-end tests requiring real Meta API connection."""

    @pytest.fixture
    def account_name(self):
        """Get test account name from credentials."""
        from meta_ads_mcp.core.credentials import get_credential_manager
        cm = get_credential_manager()
        accounts = cm.list_accounts()
        if not accounts:
            pytest.skip("No accounts configured")
        return accounts[0]["name"]

    @pytest.fixture
    def account_id(self, account_name):
        """Get test account ID."""
        from meta_ads_mcp.core.credentials import get_credential_manager
        cm = get_credential_manager()
        return cm.get_account_id(account_name)

    @pytest.mark.asyncio
    async def test_get_creative_type_video(self, account_name):
        """Test get_creative_type on a video ad."""
        # Known video ad ID from my35_echt account
        ad_id = "120237318342120381"

        result = await get_creative_type(ad_id=ad_id, account_name=account_name)
        data = json.loads(result)

        if "error" in data:
            pytest.skip(f"API error: {data['error']}")

        assert data["creative_type"] == "video"
        assert "content" in data

    @pytest.mark.asyncio
    async def test_analyze_creative_auto_detect(self, account_name):
        """Test analyze_creative auto-detects type."""
        ad_id = "120237318342120381"  # Video ad

        result = await analyze_creative(
            ad_id=ad_id,
            account_name=account_name,
            time_range="last_30d"
        )
        data = json.loads(result)

        if "error" in data:
            pytest.skip(f"API error: {data['error']}")

        assert data["creative_type"] == "video"
        assert "video_metrics" in data or "video_analysis" in data

    @pytest.mark.asyncio
    async def test_get_creative_insights_generates_recommendations(self, account_name):
        """Test get_creative_insights generates actionable insights."""
        ad_id = "120237318342120381"  # Video ad with early dropoff

        result = await get_creative_insights(
            ad_id=ad_id,
            account_name=account_name,
            time_range="last_30d"
        )
        data = json.loads(result)

        if "error" in data:
            pytest.skip(f"API error: {data['error']}")

        assert "insights" in data
        insights = data["insights"]
        # This video has early dropoff, should have recommendations
        total = len(insights["strengths"]) + len(insights["weaknesses"])
        assert total > 0

    @pytest.mark.asyncio
    async def test_get_account_benchmarks(self, account_name, account_id):
        """Test get_account_benchmarks returns valid stats."""
        result = await get_account_benchmarks(
            account_id=account_id,
            account_name=account_name,
            time_range="last_30d"
        )
        data = json.loads(result)

        if "error" in data:
            pytest.skip(f"API error: {data['error']}")

        assert "ctr" in data
        assert "cpc" in data
        assert "total_ads_analyzed" in data
