"""
Tests for library video matcher module.

Step 8.7: Unit tests for library video matching functionality.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from meta_ads_mcp.core.library_video_matcher import (
    # Data structures
    MatchMethod,
    LibraryVideo,
    VideoMatch,
    MatchingConfig,
    VideoAdInfo,
    MatchSummary,
    # Helper functions
    extract_keywords,
    match_by_name_keywords,
    aggregate_ad_performance,
    calculate_match_summary,
    # Constants
    DEFAULT_KEYWORD_PATTERNS,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_library_video_data():
    """Sample video data from Meta API /advideos endpoint."""
    return {
        "id": "123456789",
        "title": "Video 3 - Review lid.mov",
        "length": 30.5,
        "source": "https://video-source.example.com/video.mp4",
        "created_time": "2026-01-15T10:30:00+0000"
    }


@pytest.fixture
def sample_ad_data():
    """Sample ad data with video creative."""
    return {
        "id": "ad_123",
        "name": "Review testimonial ad",
        "effective_status": "ACTIVE",
        "creative": {
            "asset_feed_spec": {
                "videos": [{"video_id": "vid_999"}]
            }
        },
        "insights": {
            "data": [{
                "impressions": "5000",
                "clicks": "250",
                "spend": "50.00",
                "ctr": "5.0",
                "cpc": "0.20"
            }]
        }
    }


# =============================================================================
# Test MatchMethod Enum
# =============================================================================

class TestMatchMethod:
    """Test MatchMethod enum values."""

    def test_name_exact_value(self):
        assert MatchMethod.NAME_EXACT.value == "name_exact"

    def test_name_keyword_value(self):
        assert MatchMethod.NAME_KEYWORD.value == "name_keyword"

    def test_duration_only_value(self):
        assert MatchMethod.DURATION_ONLY.value == "duration_only"

    def test_combined_value(self):
        assert MatchMethod.COMBINED.value == "combined"


# =============================================================================
# Test LibraryVideo Dataclass
# =============================================================================

class TestLibraryVideo:
    """Test LibraryVideo dataclass."""

    def test_create_library_video(self):
        video = LibraryVideo(
            id="123",
            title="Test Video",
            duration=30.5,
            source_url="https://example.com/video.mp4",
            created_time="2026-01-15T10:30:00+0000"
        )
        assert video.id == "123"
        assert video.title == "Test Video"
        assert video.duration == 30.5
        assert video.source_url == "https://example.com/video.mp4"

    def test_from_api_response(self, sample_library_video_data):
        video = LibraryVideo.from_api_response(sample_library_video_data)
        assert video.id == "123456789"
        assert video.title == "Video 3 - Review lid.mov"
        assert video.duration == 30.5
        assert video.source_url == "https://video-source.example.com/video.mp4"

    def test_from_api_response_no_source(self):
        data = {
            "id": "123",
            "title": "Test",
            "length": 15.0
        }
        video = LibraryVideo.from_api_response(data)
        assert video.source_url is None

    def test_from_api_response_cropped_variant(self):
        data = {
            "id": "123",
            "title": "cropped_video_1.mov",
            "length": 15.0,
            "source": "https://example.com/video.mp4"
        }
        video = LibraryVideo.from_api_response(data)
        assert video.is_cropped_variant is True

    def test_to_dict(self):
        video = LibraryVideo(
            id="123",
            title="Test Video",
            duration=30.5,
            source_url="https://example.com/video.mp4"
        )
        result = video.to_dict()
        assert result["id"] == "123"
        assert result["duration_seconds"] == 30.5


# =============================================================================
# Test VideoAdInfo Dataclass
# =============================================================================

class TestVideoAdInfo:
    """Test VideoAdInfo dataclass."""

    def test_create_video_ad_info(self):
        ad = VideoAdInfo(
            ad_id="123",
            ad_name="Test Ad",
            video_ids=["vid_456"],
            status="ACTIVE"
        )
        assert ad.ad_id == "123"
        assert ad.status == "ACTIVE"
        assert ad.video_ids == ["vid_456"]

    def test_ad_info_with_performance(self):
        performance = {
            "impressions": 5000,
            "clicks": 250,
            "ctr": 5.0,
            "spend": 50.0
        }
        ad = VideoAdInfo(
            ad_id="123",
            ad_name="Test Ad",
            video_ids=["vid_456"],
            status="ACTIVE",
            performance=performance
        )
        assert ad.performance["impressions"] == 5000
        assert ad.performance["ctr"] == 5.0

    def test_to_dict(self):
        ad = VideoAdInfo(
            ad_id="123",
            ad_name="Test Ad",
            video_ids=["vid_456", "vid_789"],
            status="ACTIVE"
        )
        result = ad.to_dict()
        assert result["ad_id"] == "123"
        assert len(result["video_ids"]) == 2


# =============================================================================
# Test VideoMatch Dataclass
# =============================================================================

class TestVideoMatch:
    """Test VideoMatch dataclass."""

    def test_create_video_match(self):
        library_video = LibraryVideo(
            id="lib_123",
            title="Test Video",
            duration=30.0,
            source_url="https://example.com/video.mp4"
        )
        ad_info = VideoAdInfo(
            ad_id="ad_456",
            ad_name="Test Ad",
            video_ids=["vid_789"],
            status="ACTIVE"
        )
        match = VideoMatch(
            library_video=library_video,
            matched_ads=[ad_info],
            match_confidence=0.85,
            match_method=MatchMethod.NAME_KEYWORD,
            matched_keywords=["review"]
        )
        assert match.match_confidence == 0.85
        assert match.match_method == MatchMethod.NAME_KEYWORD
        assert len(match.matched_ads) == 1

    def test_video_match_default_performance(self):
        library_video = LibraryVideo(
            id="lib_123",
            title="Test",
            duration=30.0,
            source_url="https://example.com/video.mp4"
        )
        match = VideoMatch(
            library_video=library_video,
            matched_ads=[],
            match_confidence=0.5,
            match_method=MatchMethod.DURATION_ONLY
        )
        assert match.aggregated_performance == {}

    def test_to_dict(self):
        library_video = LibraryVideo(
            id="lib_123",
            title="Test Video",
            duration=30.0,
            source_url="https://example.com/video.mp4"
        )
        match = VideoMatch(
            library_video=library_video,
            matched_ads=[],
            match_confidence=0.75,
            match_method=MatchMethod.NAME_KEYWORD,
            matched_keywords=["review", "testimonial"]
        )
        result = match.to_dict()
        assert result["match_info"]["confidence"] == 0.75
        assert result["match_info"]["method"] == "name_keyword"


# =============================================================================
# Test MatchingConfig Dataclass
# =============================================================================

class TestMatchingConfig:
    """Test MatchingConfig dataclass."""

    def test_default_config(self):
        config = MatchingConfig()
        assert config.min_confidence_threshold == 0.5
        assert config.duration_tolerance_seconds == 1.0
        assert len(config.name_patterns) > 0  # Default patterns loaded

    def test_custom_config(self):
        config = MatchingConfig(
            min_confidence_threshold=0.7,
            duration_tolerance_seconds=2.0,
            prefer_original_over_cropped=False
        )
        assert config.min_confidence_threshold == 0.7
        assert config.prefer_original_over_cropped is False


# =============================================================================
# Test MatchSummary Dataclass
# =============================================================================

class TestMatchSummary:
    """Test MatchSummary dataclass."""

    def test_create_match_summary(self):
        summary = MatchSummary(
            total_library_videos=20,
            matched_videos=8,
            unmatched_videos=12,
            total_matched_spend=500.0
        )
        assert summary.matched_videos == 8
        assert summary.total_library_videos == 20
        assert summary.total_matched_spend == 500.0

    def test_summary_with_top_performer(self):
        summary = MatchSummary(
            total_library_videos=20,
            matched_videos=8,
            unmatched_videos=12,
            total_matched_spend=500.0,
            top_performer_pattern="review",
            top_performer_ctr=5.5
        )
        assert summary.top_performer_pattern == "review"
        assert summary.top_performer_ctr == 5.5

    def test_to_dict(self):
        summary = MatchSummary(
            total_library_videos=20,
            matched_videos=8,
            unmatched_videos=12,
            total_matched_spend=500.25
        )
        result = summary.to_dict()
        assert result["total_matched_spend"] == 500.25


# =============================================================================
# Test extract_keywords Function
# =============================================================================

class TestExtractKeywords:
    """Test keyword extraction from video/ad names."""

    def test_extract_review_keyword(self):
        keywords = extract_keywords("Video 3 - Review lid.mov", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "review" in keyword_names

    def test_extract_twijfel_keyword(self):
        keywords = extract_keywords("Twijfel video v2", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "twijfel" in keyword_names

    def test_extract_geen_tijd_keyword(self):
        keywords = extract_keywords("Geen tijd objection handler", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "geen_tijd" in keyword_names

    def test_extract_geen_zin_keyword(self):
        keywords = extract_keywords("Ik heb geen zin om te sporten", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "geen_zin" in keyword_names

    def test_extract_multiple_keywords(self):
        keywords = extract_keywords("Review video about twijfel and geen tijd", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "review" in keyword_names
        assert "twijfel" in keyword_names
        assert "geen_tijd" in keyword_names

    def test_case_insensitive(self):
        keywords = extract_keywords("TWIJFEL VIDEO REVIEW", DEFAULT_KEYWORD_PATTERNS)
        keyword_names = [k[0] for k in keywords]
        assert "twijfel" in keyword_names
        assert "review" in keyword_names

    def test_no_keywords_found(self):
        keywords = extract_keywords("Random video about cats", DEFAULT_KEYWORD_PATTERNS)
        assert len(keywords) == 0

    def test_empty_string(self):
        keywords = extract_keywords("", DEFAULT_KEYWORD_PATTERNS)
        assert len(keywords) == 0

    def test_custom_patterns(self):
        custom_patterns = [("custom", r"my_custom_pattern", "custom desc")]
        keywords = extract_keywords("video with my_custom_pattern", custom_patterns)
        keyword_names = [k[0] for k in keywords]
        assert "custom" in keyword_names

    def test_returns_matched_text(self):
        keywords = extract_keywords("Review lid video", DEFAULT_KEYWORD_PATTERNS)
        # Should return tuple with matched text
        assert any(k[1] == "review" for k in keywords)


# =============================================================================
# Test match_by_name_keywords Function
# =============================================================================

class TestMatchByNameKeywords:
    """Test keyword-based matching between library videos and ads."""

    def test_match_with_shared_keyword(self):
        library_videos = [
            LibraryVideo(
                id="lib_123",
                title="Review testimonial video",
                duration=30.0,
                source_url="https://example.com/video.mp4"
            )
        ]
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Review ad - testimonial",
                video_ids=["vid_1"],
                status="ACTIVE"
            )
        ]
        config = MatchingConfig()
        matches = match_by_name_keywords(library_videos, ads, config)
        assert len(matches) == 1
        assert matches[0].match_confidence > 0.5
        assert "review" in matches[0].matched_keywords

    def test_no_match_different_keywords(self):
        library_videos = [
            LibraryVideo(
                id="lib_123",
                title="Review video",
                duration=30.0,
                source_url="https://example.com/video.mp4"
            )
        ]
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Twijfel ad",  # Different keyword
                video_ids=["vid_1"],
                status="ACTIVE"
            )
        ]
        config = MatchingConfig()
        matches = match_by_name_keywords(library_videos, ads, config)
        # No matches because keywords don't overlap
        matching_lib_ids = [m.library_video.id for m in matches]
        assert "lib_123" not in matching_lib_ids

    def test_multiple_videos_matched(self):
        library_videos = [
            LibraryVideo(id="lib_1", title="Review video", duration=30.0, source_url="https://example.com/1.mp4"),
            LibraryVideo(id="lib_2", title="Twijfel video", duration=25.0, source_url="https://example.com/2.mp4"),
            LibraryVideo(id="lib_3", title="Random video", duration=20.0, source_url="https://example.com/3.mp4"),
        ]
        ads = [
            VideoAdInfo(ad_id="ad_1", ad_name="Review ad", video_ids=["vid_1"], status="ACTIVE"),
            VideoAdInfo(ad_id="ad_2", ad_name="Twijfel ad", video_ids=["vid_2"], status="ACTIVE"),
        ]
        config = MatchingConfig()
        matches = match_by_name_keywords(library_videos, ads, config)
        # Should match lib_1 and lib_2
        matched_ids = [m.library_video.id for m in matches]
        assert "lib_1" in matched_ids
        assert "lib_2" in matched_ids
        assert "lib_3" not in matched_ids


# =============================================================================
# Test aggregate_ad_performance Function
# =============================================================================

class TestAggregateAdPerformance:
    """Test performance metrics aggregation across multiple ads."""

    def test_aggregate_single_ad(self):
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Ad 1",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 25.0
                }
            )
        ]
        result = aggregate_ad_performance(ads)
        assert result["impressions"] == 1000
        assert result["clicks"] == 50
        assert result["spend"] == 25.0

    def test_aggregate_multiple_ads(self):
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Ad 1",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 25.0
                }
            ),
            VideoAdInfo(
                ad_id="ad_2",
                ad_name="Ad 2",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 2000,
                    "clicks": 100,
                    "spend": 50.0
                }
            )
        ]
        result = aggregate_ad_performance(ads)
        assert result["impressions"] == 3000
        assert result["clicks"] == 150
        assert result["spend"] == 75.0
        assert result["ad_count"] == 2

    def test_aggregate_with_missing_performance(self):
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Ad 1",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 25.0
                }
            ),
            VideoAdInfo(
                ad_id="ad_2",
                ad_name="Ad 2",
                video_ids=["vid_2"],
                status="ACTIVE"
                # No performance data - defaults to empty dict
            )
        ]
        result = aggregate_ad_performance(ads)
        assert result["impressions"] == 1000
        assert result["ad_count"] == 2

    def test_aggregate_empty_list(self):
        result = aggregate_ad_performance([])
        assert result == {}

    def test_aggregate_calculates_combined_ctr(self):
        ads = [
            VideoAdInfo(
                ad_id="ad_1",
                ad_name="Ad 1",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 25.0
                }
            ),
            VideoAdInfo(
                ad_id="ad_2",
                ad_name="Ad 2",
                video_ids=["vid_1"],
                status="ACTIVE",
                performance={
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": 25.0
                }
            )
        ]
        result = aggregate_ad_performance(ads)
        # 100 clicks / 2000 impressions = 5%
        assert result["ctr"] == 5.0


# =============================================================================
# Test calculate_match_summary Function
# =============================================================================

class TestCalculateMatchSummary:
    """Test match summary calculation."""

    def test_calculate_summary_with_matches(self):
        library_videos = [
            LibraryVideo(id="lib_1", title="Video 1", duration=30.0, source_url="https://example.com/1.mp4"),
            LibraryVideo(id="lib_2", title="Video 2", duration=25.0, source_url="https://example.com/2.mp4"),
            LibraryVideo(id="lib_3", title="Video 3", duration=20.0, source_url="https://example.com/3.mp4"),
        ]
        matches = [
            VideoMatch(
                library_video=library_videos[0],
                matched_ads=[],
                match_confidence=0.8,
                match_method=MatchMethod.NAME_KEYWORD,
                aggregated_performance={"spend": 100.0}
            ),
            VideoMatch(
                library_video=library_videos[1],
                matched_ads=[],
                match_confidence=0.7,
                match_method=MatchMethod.NAME_KEYWORD,
                aggregated_performance={"spend": 150.0}
            ),
        ]
        summary = calculate_match_summary(library_videos, matches)
        assert summary.total_library_videos == 3
        assert summary.matched_videos == 2
        assert summary.unmatched_videos == 1
        assert summary.total_matched_spend == 250.0

    def test_calculate_summary_no_matches(self):
        library_videos = [
            LibraryVideo(id="lib_1", title="Video 1", duration=30.0, source_url="https://example.com/1.mp4"),
        ]
        summary = calculate_match_summary(library_videos, [])
        assert summary.matched_videos == 0
        assert summary.unmatched_videos == 1


# =============================================================================
# Test DEFAULT_KEYWORD_PATTERNS
# =============================================================================

class TestDefaultKeywordPatterns:
    """Test default keyword patterns are properly defined."""

    def test_patterns_exist(self):
        assert len(DEFAULT_KEYWORD_PATTERNS) > 0

    def test_patterns_are_tuples(self):
        for pattern in DEFAULT_KEYWORD_PATTERNS:
            assert isinstance(pattern, tuple)
            assert len(pattern) == 3

    def test_twijfel_pattern_matches(self):
        import re
        pattern_name, regex, desc = next(
            p for p in DEFAULT_KEYWORD_PATTERNS if p[0] == "twijfel"
        )
        assert re.search(regex, "twijfel video", re.IGNORECASE) is not None

    def test_review_pattern_matches(self):
        import re
        pattern_name, regex, desc = next(
            p for p in DEFAULT_KEYWORD_PATTERNS if p[0] == "review"
        )
        assert re.search(regex, "review testimonial", re.IGNORECASE) is not None
        assert re.search(regex, "vrouwelijk lid", re.IGNORECASE) is not None

    def test_geen_tijd_pattern_matches_variants(self):
        import re
        pattern_name, regex, desc = next(
            p for p in DEFAULT_KEYWORD_PATTERNS if p[0] == "geen_tijd"
        )
        assert re.search(regex, "geen tijd", re.IGNORECASE) is not None
        assert re.search(regex, "geentijd", re.IGNORECASE) is not None
        assert re.search(regex, "probleem tijd", re.IGNORECASE) is not None
