"""
Library Video Matcher - Indirect Video Analysis (Step 8)

Matches ad account library videos to running ads using name and duration patterns.
Enables video content analysis combined with ad performance metrics when direct
video access requires Page permissions that aren't available.

Use Cases:
- Page-owned videos in ads return error #10 (permission denied)
- Token only has `ads_read` permission (no `pages_read_engagement`)
- Ad account has videos in media library (`/advideos` endpoint)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any, Union
from enum import Enum
import re
import json
import logging

from .server import mcp_server
from .api import make_api_request, meta_api_tool
from .credentials import get_credential_manager

logger = logging.getLogger(__name__)


# =============================================================================
# Step 8.1: Data Structures
# =============================================================================


class MatchMethod(Enum):
    """Method used to match library video to ad."""
    NAME_EXACT = "name_exact"
    NAME_KEYWORD = "name_keyword"
    DURATION_ONLY = "duration_only"
    COMBINED = "combined"


@dataclass
class LibraryVideo:
    """
    Represents a video from the ad account's media library (/advideos endpoint).

    Step 8.1.1: Library video data structure
    """
    id: str
    title: str
    duration: float  # seconds
    source_url: Optional[str] = None
    created_time: Optional[str] = None
    is_cropped_variant: bool = False

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "LibraryVideo":
        """Create LibraryVideo from Meta API response."""
        title = data.get("title", "Untitled")
        is_cropped = (
            "cropped_" in title.lower() or
            "auto_cropped_" in title.lower()
        )

        return cls(
            id=data["id"],
            title=title,
            duration=float(data.get("length", 0)),
            source_url=data.get("source"),
            created_time=data.get("created_time"),
            is_cropped_variant=is_cropped
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "duration_seconds": self.duration,
            "source_url": self.source_url,
            "created_time": self.created_time,
            "is_cropped_variant": self.is_cropped_variant
        }


@dataclass
class VideoAdInfo:
    """Information about an ad that uses video creative."""
    ad_id: str
    ad_name: str
    video_ids: List[str]
    status: str
    performance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ad_id": self.ad_id,
            "ad_name": self.ad_name,
            "video_ids": self.video_ids,
            "status": self.status,
            "performance": self.performance
        }


@dataclass
class VideoMatch:
    """
    Result of matching a library video to running ads.

    Step 8.1.2: Matching result structure
    """
    library_video: LibraryVideo
    matched_ads: List[VideoAdInfo]
    match_confidence: float  # 0.0-1.0
    match_method: MatchMethod
    matched_keywords: List[str] = field(default_factory=list)
    aggregated_performance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "library_video": self.library_video.to_dict(),
            "match_info": {
                "confidence": self.match_confidence,
                "method": self.match_method.value,
                "matched_keywords": self.matched_keywords,
                "matched_ad_count": len(self.matched_ads)
            },
            "matched_ads": [ad.to_dict() for ad in self.matched_ads],
            "aggregated_performance": self.aggregated_performance
        }


@dataclass
class MatchingConfig:
    """
    Configuration for video matching algorithm.

    Step 8.1.3: Matching configuration
    """
    name_patterns: List[Tuple[str, str, str]] = field(default_factory=list)
    duration_tolerance_seconds: float = 1.0
    min_confidence_threshold: float = 0.5
    prefer_original_over_cropped: bool = True

    def __post_init__(self):
        """Initialize default patterns if none provided."""
        if not self.name_patterns:
            self.name_patterns = DEFAULT_KEYWORD_PATTERNS


# Default keyword patterns for matching
# Format: (pattern_name, regex_pattern, description)
DEFAULT_KEYWORD_PATTERNS: List[Tuple[str, str, str]] = [
    ("twijfel", r"twijfel", "doubt/hesitation theme"),
    ("geen_tijd", r"geen.?tijd|probleem.*tijd", "no time objection"),
    ("geen_zin", r"geen.?zin", "no motivation objection"),
    ("review", r"review|testimonial|vrouwelijk|lid", "member testimonial"),
    ("sportschool_past", r"sportschool.*past|bij.*past", "finding right gym"),
    ("wist_je", r"wist.?je", "did you know hook"),
    ("carnaval", r"carnaval", "seasonal/carnival"),
    ("video_num", r"video.?\s*(\d+)", "numbered video reference"),
]


@dataclass
class MatchSummary:
    """Summary statistics for a matching operation."""
    total_library_videos: int
    matched_videos: int
    unmatched_videos: int
    total_matched_spend: float
    top_performer_pattern: Optional[str] = None
    top_performer_ctr: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_library_videos": self.total_library_videos,
            "matched_videos": self.matched_videos,
            "unmatched_videos": self.unmatched_videos,
            "total_matched_spend": round(self.total_matched_spend, 2),
            "top_performer": {
                "pattern": self.top_performer_pattern,
                "ctr": self.top_performer_ctr
            } if self.top_performer_pattern else None
        }


# =============================================================================
# Step 8.2: Library Video Fetching
# =============================================================================


async def fetch_library_videos(
    account_id: str,
    access_token: str,
    limit: int = 100
) -> List[LibraryVideo]:
    """
    Fetch videos from the ad account's media library.

    Step 8.2.1: Implement _fetch_library_videos()

    Args:
        account_id: Ad account ID (act_XXX)
        access_token: Meta API access token
        limit: Maximum number of videos to fetch

    Returns:
        List of LibraryVideo objects
    """
    videos = []
    endpoint = f"{account_id}/advideos"
    params = {
        "fields": "id,title,length,source,created_time",
        "limit": min(limit, 50)  # API max is 50 per page
    }

    # Fetch with pagination
    fetched = 0
    while fetched < limit:
        response = await make_api_request(endpoint, access_token, params)

        if "data" not in response:
            break

        for video_data in response["data"]:
            # Skip videos without source URLs (can't be downloaded)
            if "source" not in video_data:
                continue

            video = LibraryVideo.from_api_response(video_data)
            videos.append(video)
            fetched += 1

            if fetched >= limit:
                break

        # Check for more pages
        paging = response.get("paging", {})
        if "next" not in paging or fetched >= limit:
            break

        # Update params with cursor for next page
        cursors = paging.get("cursors", {})
        if "after" in cursors:
            params["after"] = cursors["after"]
        else:
            break

    logger.info(f"Fetched {len(videos)} library videos for {account_id}")
    return videos


async def fetch_video_ads_with_performance(
    account_id: str,
    access_token: str,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    status_filter: Optional[List[str]] = None
) -> List[VideoAdInfo]:
    """
    Fetch video ads with their performance metrics.

    Step 8.2.2: Implement _fetch_video_ads_with_performance()

    Args:
        account_id: Ad account ID (act_XXX)
        access_token: Meta API access token
        time_range: Time range for insights
        status_filter: List of statuses to filter (default: ACTIVE, PAUSED)

    Returns:
        List of VideoAdInfo objects
    """
    if status_filter is None:
        status_filter = ["ACTIVE", "PAUSED"]

    # Build insights time range clause
    if isinstance(time_range, dict):
        # Custom date range: .time_range({since: ..., until: ...})
        time_clause = f".time_range({json.dumps(time_range)})"
    else:
        # Preset: .date_preset(last_30d)
        time_clause = f".date_preset({time_range})"

    endpoint = f"{account_id}/ads"

    # Build insights fields
    insights_fields = "impressions,clicks,spend,ctr,cpc,reach,frequency"

    params = {
        "fields": f"id,name,effective_status,creative{{asset_feed_spec,object_story_spec}},insights{time_clause}{{{insights_fields}}}",
        "limit": 100,
        "filtering": json.dumps([{
            "field": "effective_status",
            "operator": "IN",
            "value": status_filter
        }])
    }

    video_ads = []

    response = await make_api_request(endpoint, access_token, params)

    if "data" not in response:
        return video_ads

    for ad_data in response["data"]:
        creative = ad_data.get("creative", {})
        asset_feed = creative.get("asset_feed_spec", {})

        # Check if this is a video ad
        if "videos" not in asset_feed:
            continue

        # Extract video IDs
        video_ids = [
            v.get("video_id")
            for v in asset_feed.get("videos", [])
            if v.get("video_id")
        ]

        if not video_ids:
            continue

        # Parse insights
        insights_data = ad_data.get("insights", {}).get("data", [{}])[0]
        performance = {
            "impressions": int(insights_data.get("impressions", 0)),
            "clicks": int(insights_data.get("clicks", 0)),
            "spend": float(insights_data.get("spend", 0)),
            "ctr": float(insights_data.get("ctr", 0)),
            "cpc": float(insights_data.get("cpc", 0)) if insights_data.get("cpc") else 0,
            "reach": int(insights_data.get("reach", 0)),
            "frequency": float(insights_data.get("frequency", 0)) if insights_data.get("frequency") else 0
        }

        video_ad = VideoAdInfo(
            ad_id=ad_data["id"],
            ad_name=ad_data.get("name", "Unnamed"),
            video_ids=video_ids,
            status=ad_data.get("effective_status", "UNKNOWN"),
            performance=performance
        )
        video_ads.append(video_ad)

    logger.info(f"Fetched {len(video_ads)} video ads for {account_id}")
    return video_ads


# =============================================================================
# Step 8.3: Pattern Matching Logic
# =============================================================================


def extract_keywords(text: str, patterns: List[Tuple[str, str, str]]) -> List[Tuple[str, str]]:
    """
    Extract keywords from text using regex patterns.

    Step 8.3.1: Implement _extract_name_patterns()

    Args:
        text: Text to search for patterns
        patterns: List of (pattern_name, regex, description) tuples

    Returns:
        List of (pattern_name, matched_text) tuples
    """
    matches = []
    text_lower = text.lower()

    for pattern_name, regex, _ in patterns:
        match = re.search(regex, text_lower, re.IGNORECASE)
        if match:
            matches.append((pattern_name, match.group(0)))

    return matches


def match_by_name_keywords(
    library_videos: List[LibraryVideo],
    video_ads: List[VideoAdInfo],
    config: MatchingConfig
) -> List[VideoMatch]:
    """
    Match library videos to ads by name keywords.

    Step 8.3.2: Implement _match_by_name_keywords()

    Args:
        library_videos: List of library videos
        video_ads: List of video ads
        config: Matching configuration

    Returns:
        List of VideoMatch objects
    """
    matches = []

    # Extract keywords from all video ads
    ad_keywords: Dict[str, List[VideoAdInfo]] = {}
    for ad in video_ads:
        keywords = extract_keywords(ad.ad_name, config.name_patterns)
        for pattern_name, _ in keywords:
            if pattern_name not in ad_keywords:
                ad_keywords[pattern_name] = []
            ad_keywords[pattern_name].append(ad)

    # Group library videos by base content (filter cropped variants)
    processed_patterns: Dict[str, LibraryVideo] = {}

    for video in library_videos:
        keywords = extract_keywords(video.title, config.name_patterns)

        if not keywords:
            continue

        for pattern_name, matched_text in keywords:
            # Skip if we already have a better (original) video for this pattern
            if pattern_name in processed_patterns:
                existing = processed_patterns[pattern_name]
                # Prefer original over cropped
                if config.prefer_original_over_cropped:
                    if existing.is_cropped_variant and not video.is_cropped_variant:
                        processed_patterns[pattern_name] = video
                    # Keep existing if it's original and current is cropped
                continue

            processed_patterns[pattern_name] = video

    # Create matches
    for pattern_name, video in processed_patterns.items():
        if pattern_name not in ad_keywords:
            continue

        matched_ads = ad_keywords[pattern_name]

        # Calculate confidence
        confidence = 0.8  # Base confidence for keyword match
        if not video.is_cropped_variant:
            confidence += 0.1  # Bonus for original video
        if len(matched_ads) > 1:
            confidence += 0.05  # Bonus for multiple ad matches

        confidence = min(confidence, 1.0)

        match = VideoMatch(
            library_video=video,
            matched_ads=matched_ads,
            match_confidence=confidence,
            match_method=MatchMethod.NAME_KEYWORD,
            matched_keywords=[pattern_name]
        )
        matches.append(match)

    return matches


def match_by_duration(
    library_videos: List[LibraryVideo],
    video_ads: List[VideoAdInfo],
    matched_video_ids: set,
    config: MatchingConfig
) -> List[VideoMatch]:
    """
    Match remaining library videos by duration.

    Step 8.3.3: Implement _match_by_duration()

    Args:
        library_videos: List of library videos
        video_ads: List of video ads
        matched_video_ids: Set of already matched video IDs
        config: Matching configuration

    Returns:
        List of VideoMatch objects (lower confidence)
    """
    # Duration-based matching is a secondary signal
    # Currently returns empty as we don't have ad video durations
    # This would be enhanced if we could get video metadata from thumbnails
    return []


def resolve_best_matches(
    name_matches: List[VideoMatch],
    duration_matches: List[VideoMatch],
    config: MatchingConfig
) -> List[VideoMatch]:
    """
    Combine and resolve best matches from different methods.

    Step 8.3.4: Implement _resolve_best_matches()

    Args:
        name_matches: Matches from name keyword matching
        duration_matches: Matches from duration matching
        config: Matching configuration

    Returns:
        Final list of resolved VideoMatch objects
    """
    all_matches = name_matches + duration_matches

    # Filter by confidence threshold
    filtered = [
        m for m in all_matches
        if m.match_confidence >= config.min_confidence_threshold
    ]

    # Sort by confidence (highest first)
    filtered.sort(key=lambda m: m.match_confidence, reverse=True)

    # Deduplicate by library video ID
    seen_videos = set()
    unique_matches = []

    for match in filtered:
        if match.library_video.id not in seen_videos:
            seen_videos.add(match.library_video.id)
            unique_matches.append(match)

    return unique_matches


# =============================================================================
# Step 8.4: Performance Aggregation
# =============================================================================


def aggregate_ad_performance(matched_ads: List[VideoAdInfo]) -> Dict[str, Any]:
    """
    Aggregate performance metrics from multiple ads.

    Step 8.4.1: Implement _aggregate_ad_performance()

    Args:
        matched_ads: List of matched video ads

    Returns:
        Aggregated performance dictionary
    """
    if not matched_ads:
        return {}

    total_impressions = sum(ad.performance.get("impressions", 0) for ad in matched_ads)
    total_clicks = sum(ad.performance.get("clicks", 0) for ad in matched_ads)
    total_spend = sum(ad.performance.get("spend", 0) for ad in matched_ads)
    total_reach = sum(ad.performance.get("reach", 0) for ad in matched_ads)

    # Calculate aggregated metrics
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    avg_frequency = sum(ad.performance.get("frequency", 0) for ad in matched_ads) / len(matched_ads)

    return {
        "impressions": total_impressions,
        "clicks": total_clicks,
        "spend": round(total_spend, 2),
        "ctr": round(avg_ctr, 2),
        "cpc": round(avg_cpc, 2),
        "reach": total_reach,
        "frequency": round(avg_frequency, 2),
        "ad_count": len(matched_ads)
    }


def calculate_match_summary(
    library_videos: List[LibraryVideo],
    matches: List[VideoMatch]
) -> MatchSummary:
    """
    Calculate summary statistics for matching operation.

    Step 8.4.2: Implement _calculate_match_summary()

    Args:
        library_videos: All library videos
        matches: Matched videos

    Returns:
        MatchSummary object
    """
    total_spend = sum(
        m.aggregated_performance.get("spend", 0)
        for m in matches
    )

    # Find top performer by CTR
    top_performer = None
    top_ctr = 0

    for match in matches:
        ctr = match.aggregated_performance.get("ctr", 0)
        if ctr > top_ctr:
            top_ctr = ctr
            top_performer = match.matched_keywords[0] if match.matched_keywords else None

    return MatchSummary(
        total_library_videos=len(library_videos),
        matched_videos=len(matches),
        unmatched_videos=len(library_videos) - len(matches),
        total_matched_spend=total_spend,
        top_performer_pattern=top_performer,
        top_performer_ctr=top_ctr if top_ctr > 0 else None
    )


# =============================================================================
# Step 8.5: Main Matching Function
# =============================================================================


async def match_library_videos_to_ads_internal(
    account_id: str,
    access_token: str,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    config: Optional[MatchingConfig] = None
) -> Tuple[List[VideoMatch], List[LibraryVideo], MatchSummary]:
    """
    Internal function to match library videos to ads.

    Args:
        account_id: Ad account ID
        access_token: Meta API access token
        time_range: Time range for performance data
        config: Matching configuration

    Returns:
        Tuple of (matches, unmatched_videos, summary)
    """
    if config is None:
        config = MatchingConfig()

    # Fetch data
    library_videos = await fetch_library_videos(account_id, access_token)
    video_ads = await fetch_video_ads_with_performance(account_id, access_token, time_range)

    if not library_videos:
        logger.warning(f"No library videos found for {account_id}")
        return [], [], MatchSummary(0, 0, 0, 0)

    if not video_ads:
        logger.warning(f"No video ads found for {account_id}")
        return [], library_videos, MatchSummary(len(library_videos), 0, len(library_videos), 0)

    # Run matching
    name_matches = match_by_name_keywords(library_videos, video_ads, config)

    # Get IDs of already matched videos
    matched_ids = {m.library_video.id for m in name_matches}

    # Try duration matching for unmatched
    duration_matches = match_by_duration(library_videos, video_ads, matched_ids, config)

    # Resolve best matches
    all_matches = resolve_best_matches(name_matches, duration_matches, config)

    # Aggregate performance for each match
    for match in all_matches:
        match.aggregated_performance = aggregate_ad_performance(match.matched_ads)

    # Find unmatched videos
    matched_ids = {m.library_video.id for m in all_matches}
    unmatched = [v for v in library_videos if v.id not in matched_ids]

    # Calculate summary
    summary = calculate_match_summary(library_videos, all_matches)

    return all_matches, unmatched, summary


# =============================================================================
# Step 8.5: MCP Tools
# =============================================================================


@mcp_server.tool()
@meta_api_tool
async def match_library_videos_to_ads(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: str = "last_30d",
    min_confidence: float = 0.5,
    include_unmatched: bool = False
) -> str:
    """
    Match ad account library videos to running ads using name/duration patterns.

    Use this when direct video access requires Page permissions.
    Returns library videos with their matched ad performance data.

    Args:
        account_id: Ad account ID (act_XXX)
        account_name: Optional account name for multi-tenant auth
        time_range: Performance data time range (e.g., "last_30d", "last_7d")
        min_confidence: Minimum match confidence (0.0-1.0)
        include_unmatched: Include library videos with no ad matches

    Returns:
        JSON with matched videos, performance data, and match confidence
    """
    # Token is resolved by @meta_api_tool decorator
    assert access_token is not None, "access_token required"

    config = MatchingConfig(min_confidence_threshold=min_confidence)

    matches, unmatched, summary = await match_library_videos_to_ads_internal(
        account_id, access_token, time_range, config
    )

    # Build response
    result = {
        "match_summary": summary.to_dict(),
        "matched_videos": [m.to_dict() for m in matches],
        "time_range": time_range
    }

    if include_unmatched:
        result["unmatched_videos"] = [
            {
                "id": v.id,
                "title": v.title,
                "duration_seconds": v.duration,
                "reason": "No matching ad name patterns found"
            }
            for v in unmatched
        ]

    # Add performance ranking
    if matches:
        by_spend = sorted(matches, key=lambda m: m.aggregated_performance.get("spend", 0), reverse=True)
        by_ctr = sorted(matches, key=lambda m: m.aggregated_performance.get("ctr", 0), reverse=True)

        result["performance_ranking"] = {
            "by_spend": [m.matched_keywords[0] if m.matched_keywords else m.library_video.id for m in by_spend[:5]],
            "by_ctr": [m.matched_keywords[0] if m.matched_keywords else m.library_video.id for m in by_ctr[:5]]
        }

    return json.dumps(result, indent=2)


@mcp_server.tool()
@meta_api_tool
async def analyze_matched_video(
    library_video_id: str,
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: str = "last_30d",
    extract_frames: bool = True,
    extract_subtitles: bool = True
) -> str:
    """
    Analyze a library video and combine with matched ad performance.

    Downloads video from library (no Page permissions needed),
    extracts frames and text, then combines with ad performance data.

    Args:
        library_video_id: Video ID from advideos library
        account_id: Ad account ID for performance data
        account_name: Optional account name for multi-tenant auth
        time_range: Performance data time range
        extract_frames: Enable frame extraction (requires ffmpeg)
        extract_subtitles: Enable OCR text detection (requires tesseract)

    Returns:
        Complete analysis with video content + ad performance
    """
    # Token is resolved by @meta_api_tool decorator
    assert access_token is not None, "access_token required"

    # Import video processing module
    from . import video_processing

    # Fetch video details
    endpoint = library_video_id
    params = {"fields": "id,title,length,source,created_time"}
    video_data = await make_api_request(endpoint, access_token, params)

    if "error" in video_data:
        return json.dumps({
            "error": f"Failed to fetch video: {video_data['error'].get('message', 'Unknown error')}"
        })

    library_video = LibraryVideo.from_api_response(video_data)

    # Match to ads for performance data
    config = MatchingConfig()
    matches, _, _ = await match_library_videos_to_ads_internal(
        account_id, access_token, time_range, config
    )

    # Find matching performance data
    matched_performance = None
    matched_ads_info = []
    match_confidence = 0

    for match in matches:
        if match.library_video.id == library_video_id:
            matched_performance = match.aggregated_performance
            matched_ads_info = [ad.ad_name for ad in match.matched_ads]
            match_confidence = match.match_confidence
            break

    # Build result
    result = {
        "analysis_type": "library_match",
        "library_video_id": library_video_id,
        "video_details": library_video.to_dict()
    }

    # Add content analysis if video processing is available
    if extract_frames and library_video.source_url:
        try:
            # Download and process video
            async with video_processing.VideoProcessingContext() as ctx:
                video_path = ctx.get_video_path("library_video.mp4")
                file_size = await video_processing.download_video_from_url(
                    library_video.source_url,
                    video_path
                )

                if file_size and ctx.temp_dir:
                    # Get metadata
                    metadata = await video_processing.get_video_metadata_ffprobe(video_path)

                    # Extract frames
                    frames = await video_processing.extract_frames(
                        video_path,
                        ctx.temp_dir,
                        video_processing.VideoConfig()
                    )

                    # Run OCR if enabled using batch processing
                    detected_text = []
                    if extract_subtitles and frames:
                        # Limit to first 10 frames
                        frames_to_process = frames[:10]
                        text_regions = await video_processing.detect_subtitles_batch(
                            frames_to_process
                        )
                        for region in text_regions:
                            detected_text.append({
                                "timestamp": region.timestamp,
                                "text": region.text,
                                "confidence": region.confidence
                            })

                    result["content_analysis"] = {
                        "frames_extracted": len(frames),
                        "detected_text": detected_text,
                        "video_metadata": {
                            "resolution": f"{metadata.width}x{metadata.height}" if metadata else "unknown",
                            "fps": metadata.fps if metadata else None,
                            "codec": metadata.codec if metadata else None
                        }
                    }
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            result["content_analysis"] = {
                "error": str(e),
                "frames_extracted": 0
            }

    # Add performance data
    if matched_performance:
        result["matched_ad_performance"] = {
            "matched_ads": matched_ads_info,
            "match_confidence": match_confidence,
            "time_range": time_range,
            **matched_performance
        }
    else:
        result["matched_ad_performance"] = {
            "matched_ads": [],
            "match_confidence": 0,
            "note": "No matching ads found for this video"
        }

    return json.dumps(result, indent=2)


@mcp_server.tool()
@meta_api_tool
async def analyze_all_matched_videos(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: str = "last_30d",
    limit: int = 10,
    sort_by: str = "spend"
) -> str:
    """
    Analyze all matched library videos for an account.

    Matches library videos to ads, then returns analysis for top performers.

    Args:
        account_id: Ad account ID
        account_name: Optional account name for multi-tenant auth
        time_range: Performance data time range
        limit: Max videos to analyze (sorted by sort_by)
        sort_by: Sort matched videos by this metric ("spend", "ctr", "impressions")

    Returns:
        Batch analysis with all matched videos and insights
    """
    # Token is resolved by @meta_api_tool decorator
    assert access_token is not None, "access_token required"

    config = MatchingConfig()

    matches, unmatched, summary = await match_library_videos_to_ads_internal(
        account_id, access_token, time_range, config
    )

    # Sort matches
    sort_key = lambda m: m.aggregated_performance.get(sort_by, 0)
    sorted_matches = sorted(matches, key=sort_key, reverse=True)[:limit]

    result = {
        "account_id": account_id,
        "time_range": time_range,
        "summary": summary.to_dict(),
        "analyzed_videos": [
            {
                "library_video": m.library_video.to_dict(),
                "match_info": {
                    "confidence": m.match_confidence,
                    "method": m.match_method.value,
                    "keywords": m.matched_keywords
                },
                "performance": m.aggregated_performance,
                "matched_ads": [ad.ad_name for ad in m.matched_ads]
            }
            for m in sorted_matches
        ],
        "insights": {
            "total_matched_spend": summary.total_matched_spend,
            "avg_ctr": round(
                sum(m.aggregated_performance.get("ctr", 0) for m in matches) / len(matches), 2
            ) if matches else 0,
            "top_performer": summary.top_performer_pattern,
            "recommendations": []
        }
    }

    # Generate simple recommendations
    if matches:
        avg_ctr = result["insights"]["avg_ctr"]
        for m in sorted_matches[:3]:
            ctr = m.aggregated_performance.get("ctr", 0)
            if ctr > avg_ctr * 1.2:
                result["insights"]["recommendations"].append(
                    f"'{m.matched_keywords[0] if m.matched_keywords else 'video'}' performs {int((ctr/avg_ctr - 1) * 100)}% above average - consider increasing budget"
                )
            elif ctr < avg_ctr * 0.8:
                result["insights"]["recommendations"].append(
                    f"'{m.matched_keywords[0] if m.matched_keywords else 'video'}' performs below average - consider testing new creative"
                )

    return json.dumps(result, indent=2)
