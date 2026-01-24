"""Creative Analysis functionality for Meta Ads API.

This module provides tools for analyzing ad creatives (images and videos),
combining visual analysis with performance metrics to generate insights.
"""

import json
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .api import meta_api_tool, make_api_request
from .utils import logger, extract_creative_image_urls, download_image
from .server import mcp_server
from .video_processing import (
    VideoConfig,
    VideoProcessingResult,
    process_video,
    check_ffmpeg_available,
    DEFAULT_CONFIG as VIDEO_DEFAULT_CONFIG
)


# =============================================================================
# Exceptions
# =============================================================================

class CreativeAnalysisError(Exception):
    """Base exception for creative analysis errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.message,
            "error_type": self.__class__.__name__,
            "details": self.details
        }


class VideoProcessingError(CreativeAnalysisError):
    """Exception for video processing errors (ffmpeg, download, etc.)."""
    pass


class CreativeNotFoundError(CreativeAnalysisError):
    """Exception when creative cannot be found or accessed."""
    pass


# =============================================================================
# Enums and Constants
# =============================================================================

class CreativeType(str, Enum):
    """Types of ad creatives."""
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    UNKNOWN = "unknown"


class AnalysisLevel(str, Enum):
    """Level of analysis performed (for fallback hierarchy)."""
    FULL = "full"                    # Full video/image analysis with frames
    THUMBNAIL_ONLY = "thumbnail_only"  # Only thumbnail available
    METADATA_ONLY = "metadata_only"    # Only ad copy and metrics


# =============================================================================
# Video Analysis Methodology
# =============================================================================
#
# When analyzing video creatives, follow this structured approach:
#
# 1. SUBTITLE EXTRACTION (What is being said)
#    - Extract EVERY subtitle from every frame (1 frame per second minimum)
#    - Focus on identifying:
#      * Hook (0-3 seconds): What grabs attention?
#      * Angle/Promise: What benefit/outcome is promised?
#      * Social Proof: Testimonials, results, transformations
#      * Call to Action: What action is requested?
#    - Clean OCR text and group by timestamp
#    - Map subtitles to retention curve to identify content-performance correlation
#
# 2. FRAME VISUAL ANALYSIS (What is in the frame)
#    For each key frame, analyze:
#      * Person: Man/Woman, Young/Middle-aged/Old
#      * Expression: Smiling, Talking, Neutral, Excited
#      * Eye Contact: Looking at camera (direct) or away (candid)
#      * Setting: Indoor/Outdoor, Gym/Home/Office/Nature
#      * Scene Type: Talking head, B-roll, Product shot, Text overlay
#      * Motion: Static, Moving, Fast cuts
#      * Text Overlays: Any on-screen text/graphics
#
# 3. PERFORMANCE CORRELATION
#    Combine visual + subtitle analysis with:
#      * Retention curve (where do viewers drop off?)
#      * CTR, CPC, CPM benchmarks
#      * Video engagement metrics (thruplay, watch time)
#    Map specific content to specific drop-off points
#
# 4. INSIGHTS & RECOMMENDATIONS
#    Based on the analysis, identify:
#      * Key Issues: What's causing poor performance?
#      * Strengths: What's working well?
#      * Recommendations: Specific, actionable improvements
#        - Hook improvements
#        - Pacing/structure changes
#        - Visual variety suggestions
#        - CTA timing optimization
#
# =============================================================================


@dataclass
class FrameVisualAnalysis:
    """Visual analysis of a single video frame."""
    timestamp: float

    # Person analysis
    person_visible: bool = False
    person_gender: Optional[str] = None  # "male", "female", "unknown"
    person_age_group: Optional[str] = None  # "young", "middle", "old"
    person_expression: Optional[str] = None  # "smiling", "talking", "neutral", "excited"
    eye_contact: Optional[str] = None  # "direct" (at camera), "away", "none"

    # Setting analysis
    setting: Optional[str] = None  # "indoor", "outdoor"
    location_type: Optional[str] = None  # "gym", "home", "office", "nature", "studio"

    # Scene analysis
    scene_type: Optional[str] = None  # "talking_head", "broll", "product", "text_overlay", "testimonial"
    has_text_overlay: bool = False
    text_overlay_content: Optional[str] = None
    is_scene_change: bool = False

    # Motion
    motion_level: Optional[str] = None  # "static", "slow", "dynamic", "fast_cuts"


@dataclass
class SubtitleSegment:
    """A subtitle/text segment extracted from video."""
    start_time: float
    end_time: float
    text: str
    confidence: float

    # Content classification
    content_type: Optional[str] = None  # "hook", "benefit", "social_proof", "cta", "story", "question"
    is_hook: bool = False  # First 3 seconds
    is_key_message: bool = False  # Important benefit/outcome


@dataclass
class ContentRetentionMapping:
    """Maps content to retention/performance data."""
    timestamp: float
    subtitle_text: Optional[str]
    frame_description: Optional[str]
    retention_percent: float
    drop_from_previous: float

    # Performance assessment
    performance_status: str  # "good", "warning", "critical"
    issue_detected: Optional[str] = None


@dataclass
class VideoCreativeAnalysis:
    """Complete video creative analysis result."""
    # Basic info
    ad_id: str
    ad_name: str
    video_duration: float

    # Subtitle analysis
    subtitles: List[SubtitleSegment]
    hook_text: Optional[str]  # What's said in first 3 seconds
    key_messages: List[str]  # Main benefits/outcomes mentioned
    cta_text: Optional[str]  # Call to action text

    # Visual analysis
    frame_analyses: List[FrameVisualAnalysis]
    primary_speaker: Optional[Dict[str, Any]]  # Gender, age, etc. of main person
    scene_variety_score: float  # 0-1, higher = more visual variety

    # Performance correlation
    content_retention_map: List[ContentRetentionMapping]
    critical_dropoff_content: List[Dict[str, Any]]  # What content appears at dropoff points

    # Insights
    key_issues: List[Dict[str, Any]]
    strengths: List[str]
    recommendations: List[Dict[str, Any]]


# Video analysis configuration
VIDEO_ANALYSIS_CONFIG = {
    "min_frames_per_second": 1,  # Extract at least 1 frame/second
    "hook_window_seconds": 3,  # First 3 seconds = hook
    "critical_dropoff_threshold": 20,  # % drop that's considered critical
    "ocr_confidence_threshold": 0.4,  # Minimum OCR confidence
    "subtitle_region_percent": 0.30,  # Bottom 30% of frame for subtitles
}


# =============================================================================
# Output Schemas (TypedDicts/Dataclasses)
# =============================================================================

@dataclass
class CreativeDimensions:
    """Dimensions of a creative asset."""
    width: int
    height: int
    aspect_ratio: str


@dataclass
class CreativeContent:
    """Extracted text content from a creative."""
    headlines: List[str]
    primary_texts: List[str]
    descriptions: List[str]
    call_to_action: Optional[str]
    link_url: Optional[str]


@dataclass
class VisualAnalysis:
    """Visual analysis results for a creative."""
    dimensions: Optional[CreativeDimensions]
    thumbnail_url: Optional[str]
    image_url: Optional[str]
    video_duration_seconds: Optional[float]
    frames_analyzed: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for a creative."""
    time_range: str
    impressions: int
    clicks: int
    ctr: float
    spend: float
    cpc: Optional[float]
    cpm: Optional[float]
    reach: Optional[int]
    frequency: Optional[float]


@dataclass
class CreativeAnalysisResult:
    """Complete result of creative analysis."""
    ad_id: str
    ad_name: str
    creative_type: str
    analysis_level: str
    visual_analysis: Dict[str, Any]
    content: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]]
    account_id: str


# =============================================================================
# Helper Functions
# =============================================================================

def _detect_creative_type(creative_data: Dict[str, Any]) -> Tuple[CreativeType, Dict[str, Any]]:
    """
    Detect the type of creative from its metadata.

    Args:
        creative_data: Creative metadata from Meta API

    Returns:
        Tuple of (CreativeType, relevant_data_dict)
    """
    object_story_spec = creative_data.get("object_story_spec", {})
    asset_feed_spec = creative_data.get("asset_feed_spec", {})

    # Check for video
    if "video_data" in object_story_spec:
        return CreativeType.VIDEO, object_story_spec.get("video_data", {})

    # Check for video in asset_feed_spec
    if "videos" in asset_feed_spec and asset_feed_spec["videos"]:
        return CreativeType.VIDEO, {"videos": asset_feed_spec["videos"]}

    # Check for carousel (multiple attachments)
    link_data = object_story_spec.get("link_data", {})
    if "child_attachments" in link_data and link_data["child_attachments"]:
        return CreativeType.CAROUSEL, {"child_attachments": link_data["child_attachments"]}

    # Check for image in various locations
    if "image_hash" in link_data or "picture" in link_data:
        return CreativeType.IMAGE, link_data

    if "images" in asset_feed_spec and asset_feed_spec["images"]:
        return CreativeType.IMAGE, {"images": asset_feed_spec["images"]}

    # Default to image if we have any image-related fields
    if creative_data.get("thumbnail_url") or creative_data.get("image_url"):
        return CreativeType.IMAGE, creative_data

    return CreativeType.UNKNOWN, creative_data


def _extract_creative_content(creative_data: Dict[str, Any]) -> CreativeContent:
    """
    Extract text content (headlines, body, CTA) from creative metadata.

    Args:
        creative_data: Creative metadata from Meta API

    Returns:
        CreativeContent with extracted text elements
    """
    headlines: List[str] = []
    primary_texts: List[str] = []
    descriptions: List[str] = []
    call_to_action: Optional[str] = None
    link_url: Optional[str] = None

    object_story_spec = creative_data.get("object_story_spec", {})
    asset_feed_spec = creative_data.get("asset_feed_spec", {})
    link_data = object_story_spec.get("link_data", {})
    video_data = object_story_spec.get("video_data", {})

    # Extract headlines
    # 1. From asset_feed_spec (flexible/Advantage+ ads)
    if "titles" in asset_feed_spec:
        for title in asset_feed_spec["titles"]:
            if isinstance(title, dict) and "text" in title:
                headlines.append(title["text"])
            elif isinstance(title, str):
                headlines.append(title)

    # 2. From link_data (standard ads)
    if "name" in link_data and link_data["name"]:
        if link_data["name"] not in headlines:
            headlines.append(link_data["name"])

    # 3. From video_data
    if "title" in video_data and video_data["title"]:
        if video_data["title"] not in headlines:
            headlines.append(video_data["title"])

    # Extract primary texts (body)
    # 1. From asset_feed_spec
    if "bodies" in asset_feed_spec:
        for body in asset_feed_spec["bodies"]:
            if isinstance(body, dict) and "text" in body:
                primary_texts.append(body["text"])
            elif isinstance(body, str):
                primary_texts.append(body)

    # 2. From link_data.message or video_data.message
    if "message" in link_data and link_data["message"]:
        if link_data["message"] not in primary_texts:
            primary_texts.append(link_data["message"])

    if "message" in video_data and video_data["message"]:
        if video_data["message"] not in primary_texts:
            primary_texts.append(video_data["message"])

    # Extract descriptions
    # 1. From asset_feed_spec
    if "descriptions" in asset_feed_spec:
        for desc in asset_feed_spec["descriptions"]:
            if isinstance(desc, dict) and "text" in desc:
                descriptions.append(desc["text"])
            elif isinstance(desc, str):
                descriptions.append(desc)

    # 2. From link_data.description
    if "description" in link_data and link_data["description"]:
        if link_data["description"] not in descriptions:
            descriptions.append(link_data["description"])

    # Extract CTA
    # 1. From asset_feed_spec
    if "call_to_action_types" in asset_feed_spec:
        cta_types = asset_feed_spec["call_to_action_types"]
        if cta_types:
            call_to_action = cta_types[0] if isinstance(cta_types, list) else cta_types

    # 2. From link_data or video_data
    if not call_to_action:
        for spec in [link_data, video_data]:
            if "call_to_action" in spec:
                cta = spec["call_to_action"]
                if isinstance(cta, dict) and "type" in cta:
                    call_to_action = cta["type"]
                elif isinstance(cta, str):
                    call_to_action = cta
                break

    # Extract link URL
    # 1. From asset_feed_spec
    if "link_urls" in asset_feed_spec:
        urls = asset_feed_spec["link_urls"]
        if urls:
            url = urls[0] if isinstance(urls, list) else urls
            if isinstance(url, dict) and "website_url" in url:
                link_url = url["website_url"]
            elif isinstance(url, str):
                link_url = url

    # 2. From link_data
    if not link_url and "link" in link_data:
        link_url = link_data["link"]

    return CreativeContent(
        headlines=headlines,
        primary_texts=primary_texts,
        descriptions=descriptions,
        call_to_action=call_to_action,
        link_url=link_url
    )


async def _fetch_creative_metadata(
    ad_id: str,
    access_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch complete creative metadata for an ad.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Optional access token

    Returns:
        Dict with ad and creative metadata
    """
    # Fetch ad with creative details
    fields = (
        "id,name,status,account_id,"
        "creative{id,name,status,thumbnail_url,image_url,image_hash,"
        "object_story_spec,asset_feed_spec,video_id}"
    )

    endpoint = f"{ad_id}"
    params = {"fields": fields}

    data = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        raise CreativeNotFoundError(
            f"Failed to fetch ad {ad_id}",
            details=data.get("error", {})
        )

    return data


async def _fetch_performance_metrics(
    ad_id: str,
    time_range: Union[str, Dict[str, str]],
    access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch performance metrics for an ad.

    Args:
        ad_id: Meta Ads ad ID
        time_range: Time range preset or custom dict
        access_token: Optional access token

    Returns:
        Dict with performance metrics or None if unavailable
    """
    endpoint = f"{ad_id}/insights"
    params = {
        "fields": "impressions,clicks,ctr,spend,cpc,cpm,reach,frequency,actions"
    }

    # Handle time_range
    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        logger.warning(f"Failed to fetch metrics for ad {ad_id}: {data.get('error')}")
        return None

    # Extract first result (should be only one for single ad)
    insights = data.get("data", [])
    if not insights:
        return None

    return insights[0]


def _parse_performance_metrics(
    raw_metrics: Dict[str, Any],
    time_range: Union[str, Dict[str, str]]
) -> PerformanceMetrics:
    """
    Parse raw API metrics into structured PerformanceMetrics.

    Args:
        raw_metrics: Raw metrics dict from Meta API
        time_range: Time range used for the query

    Returns:
        PerformanceMetrics dataclass
    """
    # Convert time_range to string for display
    if isinstance(time_range, dict):
        time_range_str = f"{time_range.get('since', '')} to {time_range.get('until', '')}"
    else:
        time_range_str = time_range

    return PerformanceMetrics(
        time_range=time_range_str,
        impressions=int(raw_metrics.get("impressions", 0)),
        clicks=int(raw_metrics.get("clicks", 0)),
        ctr=float(raw_metrics.get("ctr", 0)),
        spend=float(raw_metrics.get("spend", 0)),
        cpc=float(raw_metrics["cpc"]) if raw_metrics.get("cpc") else None,
        cpm=float(raw_metrics["cpm"]) if raw_metrics.get("cpm") else None,
        reach=int(raw_metrics["reach"]) if raw_metrics.get("reach") else None,
        frequency=float(raw_metrics["frequency"]) if raw_metrics.get("frequency") else None
    )


async def _fetch_image_analysis(
    creative_data: Dict[str, Any],
    account_id: str,
    access_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch and analyze image data from a creative.

    Extracts image URLs, downloads the image to get dimensions,
    and returns structured visual analysis data.

    Args:
        creative_data: Creative metadata from Meta API
        account_id: Ad account ID for fetching full-size images
        access_token: Optional access token

    Returns:
        Dict with image analysis including dimensions and URLs
    """
    result = {
        "image_urls": [],
        "thumbnail_url": None,
        "dimensions": None,
        "image_hash": None,
        "analysis_level": AnalysisLevel.METADATA_ONLY.value
    }

    # Extract thumbnail URL
    result["thumbnail_url"] = creative_data.get("thumbnail_url")

    # Extract image URLs using utility function
    image_urls = extract_creative_image_urls(creative_data)
    result["image_urls"] = image_urls

    # Extract image hash from various locations
    image_hash = None
    object_story_spec = creative_data.get("object_story_spec", {})
    asset_feed_spec = creative_data.get("asset_feed_spec", {})
    link_data = object_story_spec.get("link_data", {})

    # Check direct image_hash on creative
    if "image_hash" in creative_data:
        image_hash = creative_data["image_hash"]
    # Check link_data
    elif "image_hash" in link_data:
        image_hash = link_data["image_hash"]
    # Check asset_feed_spec images
    elif "images" in asset_feed_spec and asset_feed_spec["images"]:
        first_image = asset_feed_spec["images"][0]
        if "hash" in first_image:
            image_hash = first_image["hash"]

    result["image_hash"] = image_hash

    # If we have an image hash, try to fetch full image data with dimensions
    if image_hash and account_id:
        try:
            # Ensure account_id has act_ prefix
            if not account_id.startswith("act_"):
                account_id = f"act_{account_id}"

            image_endpoint = f"{account_id}/adimages"
            hashes_str = f'["{image_hash}"]'
            image_params = {
                "fields": "hash,url,width,height,name,status",
                "hashes": hashes_str
            }

            image_data = await make_api_request(image_endpoint, access_token, image_params)

            if "data" in image_data and image_data["data"]:
                first_image = image_data["data"][0]
                width = first_image.get("width")
                height = first_image.get("height")

                if width and height:
                    # Calculate aspect ratio
                    from math import gcd
                    divisor = gcd(width, height)
                    aspect_w = width // divisor
                    aspect_h = height // divisor
                    aspect_ratio = f"{aspect_w}:{aspect_h}"

                    result["dimensions"] = {
                        "width": width,
                        "height": height,
                        "aspect_ratio": aspect_ratio
                    }
                    result["analysis_level"] = AnalysisLevel.FULL.value

                # Add the full-quality URL if available
                if first_image.get("url"):
                    result["full_image_url"] = first_image["url"]

        except Exception as e:
            logger.warning(f"Failed to fetch image dimensions: {e}")

    # Fallback: if we have image URLs but no dimensions, try to download and check
    if not result["dimensions"] and image_urls:
        result["analysis_level"] = AnalysisLevel.THUMBNAIL_ONLY.value

    return result


async def _calculate_benchmarks(
    account_id: str,
    time_range: Union[str, Dict[str, str]],
    creative_type: Optional[str] = None,
    access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Calculate account-level benchmarks for comparison.

    Fetches aggregated metrics for the account to compare
    individual creative performance against.

    Args:
        account_id: Ad account ID
        time_range: Time range preset or custom dict
        creative_type: Optional filter by creative type (image/video)
        access_token: Optional access token

    Returns:
        Dict with benchmark metrics (avg, percentiles) or None
    """
    # Ensure account_id has act_ prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    # Fetch ad-level insights for the account
    endpoint = f"{account_id}/insights"
    params = {
        "level": "ad",
        "fields": "ad_id,impressions,clicks,ctr,spend,cpc,cpm",
        "limit": 500  # Get enough ads for meaningful benchmarks
    }

    # Handle time_range
    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        logger.warning(f"Failed to fetch benchmarks for account {account_id}: {data.get('error')}")
        return None

    insights = data.get("data", [])
    if not insights:
        return None

    # Filter ads with meaningful data (>0 impressions)
    valid_ads = [
        ad for ad in insights
        if int(ad.get("impressions", 0)) > 0
    ]

    if len(valid_ads) < 3:
        return None  # Not enough data for meaningful benchmarks

    # Calculate statistics
    def safe_float(val):
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def calculate_percentiles(values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for a list of values."""
        if not values:
            return {"avg": 0, "p25": 0, "p50": 0, "p75": 0}

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        return {
            "avg": sum(sorted_vals) / n,
            "p25": sorted_vals[int(n * 0.25)] if n > 0 else 0,
            "p50": sorted_vals[int(n * 0.50)] if n > 0 else 0,
            "p75": sorted_vals[int(n * 0.75)] if n > 0 else 0,
            "min": sorted_vals[0] if n > 0 else 0,
            "max": sorted_vals[-1] if n > 0 else 0
        }

    # Extract metrics
    ctrs = [safe_float(ad.get("ctr")) for ad in valid_ads if ad.get("ctr")]
    cpcs = [safe_float(ad.get("cpc")) for ad in valid_ads if ad.get("cpc")]
    cpms = [safe_float(ad.get("cpm")) for ad in valid_ads if ad.get("cpm")]

    benchmarks = {
        "total_ads_analyzed": len(valid_ads),
        "time_range": time_range if isinstance(time_range, str) else f"{time_range.get('since')} to {time_range.get('until')}",
        "ctr": calculate_percentiles(ctrs),
        "cpc": calculate_percentiles(cpcs),
        "cpm": calculate_percentiles(cpms)
    }

    return benchmarks


def _compare_to_benchmarks(
    metrics: PerformanceMetrics,
    benchmarks: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare creative metrics to account benchmarks.

    Args:
        metrics: Performance metrics for the creative
        benchmarks: Account-level benchmark data

    Returns:
        Dict with comparison results
    """
    comparison = {}

    # Compare CTR
    if metrics.ctr and benchmarks.get("ctr", {}).get("avg"):
        ctr_avg = benchmarks["ctr"]["avg"]
        ctr_diff = ((metrics.ctr - ctr_avg) / ctr_avg) * 100 if ctr_avg else 0
        comparison["ctr"] = {
            "value": metrics.ctr,
            "account_avg": ctr_avg,
            "diff_percent": round(ctr_diff, 1),
            "performance": "above" if ctr_diff > 5 else "below" if ctr_diff < -5 else "average"
        }

    # Compare CPC (lower is better)
    if metrics.cpc and benchmarks.get("cpc", {}).get("avg"):
        cpc_avg = benchmarks["cpc"]["avg"]
        cpc_diff = ((metrics.cpc - cpc_avg) / cpc_avg) * 100 if cpc_avg else 0
        comparison["cpc"] = {
            "value": metrics.cpc,
            "account_avg": cpc_avg,
            "diff_percent": round(cpc_diff, 1),
            "performance": "below" if cpc_diff < -5 else "above" if cpc_diff > 5 else "average"
        }

    # Compare CPM (lower is generally better)
    if metrics.cpm and benchmarks.get("cpm", {}).get("avg"):
        cpm_avg = benchmarks["cpm"]["avg"]
        cpm_diff = ((metrics.cpm - cpm_avg) / cpm_avg) * 100 if cpm_avg else 0
        comparison["cpm"] = {
            "value": metrics.cpm,
            "account_avg": cpm_avg,
            "diff_percent": round(cpm_diff, 1),
            "performance": "below" if cpm_diff < -5 else "above" if cpm_diff > 5 else "average"
        }

    # Determine overall performance tier
    scores = []
    if "ctr" in comparison:
        # Higher CTR is better
        scores.append(1 if comparison["ctr"]["performance"] == "above" else -1 if comparison["ctr"]["performance"] == "below" else 0)
    if "cpc" in comparison:
        # Lower CPC is better, so invert the score
        scores.append(1 if comparison["cpc"]["performance"] == "below" else -1 if comparison["cpc"]["performance"] == "above" else 0)

    if scores:
        avg_score = sum(scores) / len(scores)
        if avg_score > 0.5:
            comparison["overall_tier"] = "top"
        elif avg_score < -0.5:
            comparison["overall_tier"] = "bottom"
        else:
            comparison["overall_tier"] = "middle"

    return comparison


# =============================================================================
# MCP Tools
# =============================================================================

@mcp_server.tool()
@meta_api_tool
async def get_creative_type(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None
) -> str:
    """
    Detect the type of creative (image, video, carousel) for an ad.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)

    Returns:
        JSON with creative type and basic metadata
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        # Fetch creative metadata
        ad_data = await _fetch_creative_metadata(ad_id, access_token)

        creative = ad_data.get("creative", {})
        creative_type, type_data = _detect_creative_type(creative)

        # Extract content
        content = _extract_creative_content(creative)

        result = {
            "ad_id": ad_id,
            "ad_name": ad_data.get("name", ""),
            "account_id": ad_data.get("account_id", ""),
            "creative_id": creative.get("id", ""),
            "creative_type": creative_type.value,
            "thumbnail_url": creative.get("thumbnail_url"),
            "content": {
                "headlines": content.headlines,
                "primary_texts": content.primary_texts,
                "descriptions": content.descriptions,
                "call_to_action": content.call_to_action,
                "link_url": content.link_url
            }
        }

        # Add video-specific fields
        if creative_type == CreativeType.VIDEO:
            result["video_id"] = creative.get("video_id")

        return json.dumps(result, indent=2)

    except CreativeAnalysisError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error detecting creative type for {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_creative_content(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None
) -> str:
    """
    Extract all text content (headlines, body, CTA) from an ad creative.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)

    Returns:
        JSON with extracted text content
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        ad_data = await _fetch_creative_metadata(ad_id, access_token)
        creative = ad_data.get("creative", {})
        content = _extract_creative_content(creative)

        result = {
            "ad_id": ad_id,
            "ad_name": ad_data.get("name", ""),
            "content": {
                "headlines": content.headlines,
                "primary_texts": content.primary_texts,
                "descriptions": content.descriptions,
                "call_to_action": content.call_to_action,
                "link_url": content.link_url
            },
            "headline_count": len(content.headlines),
            "has_cta": content.call_to_action is not None
        }

        return json.dumps(result, indent=2)

    except CreativeAnalysisError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error extracting content for {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def analyze_image_creative(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    include_benchmarks: bool = True
) -> str:
    """
    Analyze an image ad creative with performance metrics and benchmarks.

    Returns visual analysis (dimensions, URLs), text content, performance
    metrics, and comparison to account benchmarks.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)
        include_benchmarks: Whether to include account benchmarks (default: True)

    Returns:
        JSON with complete image creative analysis
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        # Fetch creative metadata
        ad_data = await _fetch_creative_metadata(ad_id, access_token)

        creative = ad_data.get("creative", {})
        account_id = ad_data.get("account_id", "")

        # Detect creative type
        creative_type, type_data = _detect_creative_type(creative)

        # Check if this is actually an image creative
        if creative_type == CreativeType.VIDEO:
            return json.dumps({
                "error": "This is a video creative, not an image creative",
                "creative_type": creative_type.value,
                "hint": "Use analyze_video_creative for video ads (coming soon)"
            }, indent=2)

        # Extract content
        content = _extract_creative_content(creative)

        # Fetch image analysis
        image_analysis = await _fetch_image_analysis(creative, account_id, access_token)

        # Fetch performance metrics
        raw_metrics = await _fetch_performance_metrics(ad_id, time_range, access_token)
        metrics = None
        metrics_dict = None
        if raw_metrics:
            metrics = _parse_performance_metrics(raw_metrics, time_range)
            metrics_dict = asdict(metrics)

        # Fetch benchmarks and compare
        benchmark_comparison = None
        if include_benchmarks and metrics and account_id:
            benchmarks = await _calculate_benchmarks(account_id, time_range, None, access_token)
            if benchmarks:
                benchmark_comparison = _compare_to_benchmarks(metrics, benchmarks)

        # Build result
        result = {
            "ad_id": ad_id,
            "ad_name": ad_data.get("name", ""),
            "account_id": account_id,
            "creative_id": creative.get("id", ""),
            "creative_type": creative_type.value,
            "analysis_level": image_analysis.get("analysis_level", AnalysisLevel.METADATA_ONLY.value),
            "visual_analysis": {
                "dimensions": image_analysis.get("dimensions"),
                "thumbnail_url": image_analysis.get("thumbnail_url"),
                "image_urls": image_analysis.get("image_urls", []),
                "full_image_url": image_analysis.get("full_image_url"),
                "image_hash": image_analysis.get("image_hash")
            },
            "content": {
                "headlines": content.headlines,
                "primary_texts": content.primary_texts,
                "descriptions": content.descriptions,
                "call_to_action": content.call_to_action,
                "link_url": content.link_url
            },
            "performance_metrics": metrics_dict,
            "benchmark_comparison": benchmark_comparison
        }

        return json.dumps(result, indent=2)

    except CreativeAnalysisError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error analyzing image creative for {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_account_benchmarks(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d"
) -> str:
    """
    Get performance benchmarks for an ad account.

    Calculates average and percentile metrics (CTR, CPC, CPM) across
    all ads in the account for the specified time range.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)

    Returns:
        JSON with benchmark statistics
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    try:
        benchmarks = await _calculate_benchmarks(account_id, time_range, None, access_token)

        if not benchmarks:
            return json.dumps({
                "error": "Not enough data to calculate benchmarks",
                "hint": "Need at least 3 ads with impressions in the time range"
            }, indent=2)

        return json.dumps(benchmarks, indent=2)

    except Exception as e:
        logger.error(f"Error fetching benchmarks for {account_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


# =============================================================================
# Video Analysis Functions
# =============================================================================

async def _fetch_video_retention_metrics(
    ad_id: str,
    time_range: Union[str, Dict[str, str]],
    access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch video-specific retention and engagement metrics.

    Args:
        ad_id: Meta Ads ad ID
        time_range: Time range preset or custom dict
        access_token: Optional access token

    Returns:
        Dict with video metrics including retention data
    """
    endpoint = f"{ad_id}/insights"
    params = {
        "fields": (
            "video_play_actions,"
            "video_p25_watched_actions,"
            "video_p50_watched_actions,"
            "video_p75_watched_actions,"
            "video_p95_watched_actions,"
            "video_p100_watched_actions,"
            "video_thruplay_watched_actions,"
            "video_avg_time_watched_actions,"
            "video_play_curve_actions"
        )
    }

    # Handle time_range
    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        logger.warning(f"Failed to fetch video metrics for {ad_id}: {data.get('error')}")
        return None

    insights = data.get("data", [])
    if not insights:
        return None

    raw = insights[0]

    # Parse video metrics
    def get_action_value(actions: List[Dict], action_type: str = "video_view") -> int:
        """Extract value from actions array."""
        if not actions:
            return 0
        for action in actions:
            if action.get("action_type") == action_type:
                return int(action.get("value", 0))
        # Fallback to first action value
        return int(actions[0].get("value", 0)) if actions else 0

    video_plays = get_action_value(raw.get("video_play_actions", []))
    p25 = get_action_value(raw.get("video_p25_watched_actions", []))
    p50 = get_action_value(raw.get("video_p50_watched_actions", []))
    p75 = get_action_value(raw.get("video_p75_watched_actions", []))
    p95 = get_action_value(raw.get("video_p95_watched_actions", []))
    p100 = get_action_value(raw.get("video_p100_watched_actions", []))
    thruplay = get_action_value(raw.get("video_thruplay_watched_actions", []))

    # Get average watch time
    avg_watch_actions = raw.get("video_avg_time_watched_actions", [])
    avg_watch_time = 0.0
    if avg_watch_actions:
        avg_watch_time = float(avg_watch_actions[0].get("value", 0))

    # Build retention curve (if available)
    retention_curve = None
    play_curve_actions = raw.get("video_play_curve_actions", [])
    if play_curve_actions and play_curve_actions[0].get("value"):
        try:
            retention_curve = json.loads(play_curve_actions[0]["value"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Calculate retention rates
    watch_completion_rate = (p100 / video_plays * 100) if video_plays > 0 else 0
    thruplay_rate = (thruplay / video_plays * 100) if video_plays > 0 else 0

    return {
        "video_plays": video_plays,
        "retention_p25": p25,
        "retention_p50": p50,
        "retention_p75": p75,
        "retention_p95": p95,
        "retention_p100": p100,
        "thruplay_count": thruplay,
        "avg_watch_time_seconds": avg_watch_time,
        "retention_curve": retention_curve,
        "watch_completion_rate": round(watch_completion_rate, 2),
        "thruplay_rate": round(thruplay_rate, 2),
        "retention_percentages": {
            "25%": round((p25 / video_plays * 100), 1) if video_plays > 0 else 0,
            "50%": round((p50 / video_plays * 100), 1) if video_plays > 0 else 0,
            "75%": round((p75 / video_plays * 100), 1) if video_plays > 0 else 0,
            "95%": round((p95 / video_plays * 100), 1) if video_plays > 0 else 0,
            "100%": round((p100 / video_plays * 100), 1) if video_plays > 0 else 0
        }
    }


def _identify_dropoff_points(
    retention_percentages: Dict[str, float],
    threshold: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Identify significant viewer drop-off points from retention data.

    Args:
        retention_percentages: Dict with retention at 25%, 50%, 75%, 95%, 100%
        threshold: Minimum percentage drop to flag

    Returns:
        List of drop-off points with timestamp estimates
    """
    dropoffs = []
    prev_rate = 100.0
    checkpoints = ["25%", "50%", "75%", "95%", "100%"]

    for checkpoint in checkpoints:
        current_rate = retention_percentages.get(checkpoint, 0)
        drop = prev_rate - current_rate

        if drop >= threshold:
            dropoffs.append({
                "checkpoint": checkpoint,
                "drop_percent": round(drop, 1),
                "remaining_viewers": round(current_rate, 1),
                "significance": "high" if drop > 20 else "medium"
            })

        prev_rate = current_rate

    return dropoffs


# =============================================================================
# Detailed Video Content Analysis Functions
# =============================================================================


def _classify_subtitle_content(text: str, timestamp: float, video_duration: float) -> Dict[str, Any]:
    """
    Classify subtitle content type based on text and timing.

    Args:
        text: The subtitle text
        timestamp: When this text appears
        video_duration: Total video duration

    Returns:
        Dict with content_type and flags
    """
    text_lower = text.lower()
    result = {
        "content_type": "story",  # Default
        "is_hook": timestamp <= VIDEO_ANALYSIS_CONFIG["hook_window_seconds"],
        "is_key_message": False,
        "is_cta": False
    }

    # Check for CTA patterns (usually near end)
    cta_keywords = ["boek", "book", "klik", "click", "probeer", "try", "start", "begin",
                    "gratis", "free", "nu", "now", "vandaag", "today", "proefles", "aanmelden"]
    if any(kw in text_lower for kw in cta_keywords) and timestamp > video_duration * 0.7:
        result["content_type"] = "cta"
        result["is_cta"] = True

    # Check for question patterns (often hooks)
    if "?" in text or text_lower.startswith(("waarom", "why", "hoe", "how", "wat", "what", "ken je", "wist je")):
        result["content_type"] = "question"

    # Check for social proof / testimonial
    proof_keywords = ["resultaat", "result", "kilo", "kg", "maand", "month", "jaar", "year",
                      "perfect", "geweldig", "amazing", "fantastisch", "beste", "best"]
    if any(kw in text_lower for kw in proof_keywords):
        result["content_type"] = "social_proof"
        result["is_key_message"] = True

    # Check for benefit/outcome mentions
    benefit_keywords = ["energie", "energy", "fit", "sterk", "strong", "gezond", "healthy",
                        "skiën", "skiing", "sporten", "exercise", "afgevallen", "lost weight",
                        "bereikt", "achieved", "gelukt", "succeeded"]
    if any(kw in text_lower for kw in benefit_keywords):
        result["content_type"] = "benefit"
        result["is_key_message"] = True

    return result


def _extract_subtitles_detailed(
    raw_subtitles: List[Dict[str, Any]],
    video_duration: float
) -> List[SubtitleSegment]:
    """
    Process raw subtitle detections into structured SubtitleSegments.

    Args:
        raw_subtitles: List of dicts with text, timestamp, confidence
        video_duration: Total video duration

    Returns:
        List of SubtitleSegment objects with classification
    """
    segments = []
    prev_end = 0.0

    for i, sub in enumerate(raw_subtitles):
        text = sub.get("text", "").strip()
        if not text or len(text) < 3:
            continue

        timestamp = sub.get("timestamp", 0.0)
        confidence = sub.get("confidence", 0.0)

        # Estimate end time (next subtitle or +2 seconds)
        if i + 1 < len(raw_subtitles):
            end_time = raw_subtitles[i + 1].get("timestamp", timestamp + 2.0)
        else:
            end_time = min(timestamp + 2.0, video_duration)

        # Classify content
        classification = _classify_subtitle_content(text, timestamp, video_duration)

        segment = SubtitleSegment(
            start_time=timestamp,
            end_time=end_time,
            text=text,
            confidence=confidence,
            content_type=classification["content_type"],
            is_hook=classification["is_hook"],
            is_key_message=classification["is_key_message"]
        )
        segments.append(segment)

    return segments


def _create_content_retention_mapping(
    subtitles: List[SubtitleSegment],
    retention_curve: List[int],
    video_duration: float
) -> List[ContentRetentionMapping]:
    """
    Map content (subtitles/frames) to retention data.

    Args:
        subtitles: Processed subtitle segments
        retention_curve: List of retention percentages at intervals
        video_duration: Total video duration

    Returns:
        List of ContentRetentionMapping objects
    """
    mappings = []

    if not retention_curve:
        return mappings

    # Calculate interval between retention data points
    interval = video_duration / len(retention_curve) if len(retention_curve) > 0 else 1.0

    prev_retention = 100.0

    for i, retention in enumerate(retention_curve):
        timestamp = i * interval

        # Find subtitle at this timestamp
        subtitle_text = None
        for sub in subtitles:
            if sub.start_time <= timestamp < sub.end_time:
                subtitle_text = sub.text
                break

        drop = prev_retention - retention

        # Determine status
        if retention >= 50:
            status = "good"
        elif retention >= 20:
            status = "warning"
        else:
            status = "critical"

        # Detect issues
        issue = None
        if drop >= VIDEO_ANALYSIS_CONFIG["critical_dropoff_threshold"]:
            if timestamp <= 3:
                issue = "Critical hook failure - viewers leaving immediately"
            elif timestamp <= 7:
                issue = "Early content not engaging enough"
            else:
                issue = f"Significant drop at {timestamp:.1f}s - content may be losing interest"

        mapping = ContentRetentionMapping(
            timestamp=timestamp,
            subtitle_text=subtitle_text,
            frame_description=None,  # To be filled by visual analysis
            retention_percent=retention,
            drop_from_previous=round(drop, 1),
            performance_status=status,
            issue_detected=issue
        )
        mappings.append(mapping)

        prev_retention = retention

    return mappings


def _identify_critical_dropoff_content(
    content_map: List[ContentRetentionMapping],
    subtitles: List[SubtitleSegment]
) -> List[Dict[str, Any]]:
    """
    Identify what content appears at critical drop-off points.

    Args:
        content_map: Content-retention mapping
        subtitles: All subtitles

    Returns:
        List of critical content moments with analysis
    """
    critical_content = []

    for mapping in content_map:
        if mapping.drop_from_previous >= VIDEO_ANALYSIS_CONFIG["critical_dropoff_threshold"]:
            # Find surrounding content
            ts = mapping.timestamp
            surrounding_subs = [
                s for s in subtitles
                if ts - 2 <= s.start_time <= ts + 2
            ]

            critical_content.append({
                "timestamp": ts,
                "retention_before": mapping.retention_percent + mapping.drop_from_previous,
                "retention_after": mapping.retention_percent,
                "drop_percent": mapping.drop_from_previous,
                "content_at_dropoff": mapping.subtitle_text,
                "surrounding_content": [s.text for s in surrounding_subs],
                "issue": mapping.issue_detected,
                "recommendation": _get_dropoff_recommendation(ts, mapping.drop_from_previous)
            })

    return critical_content


def _get_dropoff_recommendation(timestamp: float, drop_percent: float) -> str:
    """Generate specific recommendation based on dropoff timing."""
    if timestamp <= 1:
        return "Thumbnail and first frame aren't stopping the scroll. Test a more attention-grabbing opening visual."
    elif timestamp <= 3:
        return "Hook isn't compelling enough. Lead with the outcome/benefit instead of setup. Show don't tell."
    elif timestamp <= 7:
        return "Early content is too slow. Add visual variety, faster cuts, or text overlays to maintain interest."
    elif timestamp <= 15:
        return "Mid-video sag. This is often where testimonials lose viewers. Front-load the best content."
    else:
        return "Late-video drop. Consider a shorter version or move the CTA earlier while viewers are still engaged."


def _generate_video_insights_detailed(
    subtitles: List[SubtitleSegment],
    content_map: List[ContentRetentionMapping],
    critical_content: List[Dict[str, Any]],
    video_duration: float,
    metrics: Optional[Dict[str, Any]],
    video_metrics: Optional[Dict[str, Any]],
    benchmark_comparison: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate comprehensive insights from video analysis.

    Returns dict with key_issues, strengths, and recommendations.
    """
    insights = {
        "key_issues": [],
        "strengths": [],
        "recommendations": []
    }

    # Analyze hook (first 3 seconds)
    hook_subs = [s for s in subtitles if s.is_hook]
    if hook_subs:
        hook_text = " ".join([s.text for s in hook_subs])

        # Check if hook is a question (often less effective)
        if "?" in hook_text:
            insights["key_issues"].append({
                "type": "weak_hook",
                "severity": "high",
                "description": "Hook uses a question format which can signal 'this is an ad'",
                "content": hook_text,
                "impact": "Viewers scroll past before hearing the answer"
            })
            insights["recommendations"].append({
                "type": "hook_improvement",
                "priority": "high",
                "suggestion": "Replace the question with a compelling statement or outcome",
                "example": "Instead of 'Why did you choose X?' start with 'I went skiing in Italy after just 3 months!'"
            })

    # Analyze key messages timing
    key_messages = [s for s in subtitles if s.is_key_message]
    if key_messages:
        first_key_message_time = key_messages[0].start_time
        if first_key_message_time > 10:
            insights["key_issues"].append({
                "type": "late_key_message",
                "severity": "high",
                "description": f"First key benefit/outcome appears at {first_key_message_time:.1f}s",
                "content": key_messages[0].text,
                "impact": f"Only ~{_estimate_retention_at_time(content_map, first_key_message_time)}% of viewers hear this"
            })
            insights["recommendations"].append({
                "type": "content_reorder",
                "priority": "high",
                "suggestion": "Move the strongest benefit/outcome to the first 3-5 seconds",
                "example": f"Lead with: '{key_messages[0].text}'"
            })

    # Analyze CTA timing
    cta_subs = [s for s in subtitles if s.content_type == "cta"]
    if cta_subs:
        cta_time = cta_subs[0].start_time
        cta_retention = _estimate_retention_at_time(content_map, cta_time)
        if cta_retention < 10:
            insights["key_issues"].append({
                "type": "late_cta",
                "severity": "medium",
                "description": f"CTA appears at {cta_time:.1f}s when only ~{cta_retention}% are watching",
                "content": cta_subs[0].text,
                "impact": "Most viewers never see the call to action"
            })
            insights["recommendations"].append({
                "type": "cta_timing",
                "priority": "medium",
                "suggestion": "Show CTA earlier or create a shorter video version"
            })

    # Add critical dropoff issues
    for cc in critical_content:
        insights["key_issues"].append({
            "type": "critical_dropoff",
            "severity": "high" if cc["drop_percent"] > 30 else "medium",
            "description": f"{cc['drop_percent']:.0f}% drop at {cc['timestamp']:.1f}s",
            "content": cc["content_at_dropoff"],
            "impact": cc["issue"]
        })

    # Analyze strengths from benchmark comparison
    if benchmark_comparison:
        if benchmark_comparison.get("ctr", {}).get("performance") == "above":
            insights["strengths"].append(
                f"Strong CTR ({benchmark_comparison['ctr']['value']:.2f}%) - "
                f"{benchmark_comparison['ctr']['diff_percent']:+.1f}% vs account average"
            )

    # Analyze video metrics strengths
    if video_metrics:
        thruplay_rate = video_metrics.get("thruplay_rate", 0)
        if thruplay_rate > 10:
            insights["strengths"].append(f"Good thruplay rate ({thruplay_rate:.1f}%)")

        # Check if retention stabilizes
        retention_pcts = video_metrics.get("retention_percentages", {})
        if retention_pcts:
            mid_retention = retention_pcts.get("50%", 0)
            late_retention = retention_pcts.get("75%", 0)
            if mid_retention > 0 and late_retention > 0:
                late_drop = mid_retention - late_retention
                if late_drop < 5:
                    insights["strengths"].append(
                        f"Strong retention after midpoint (only {late_drop:.0f}% drop from 50% to 75%)"
                    )

    return insights


def _estimate_retention_at_time(content_map: List[ContentRetentionMapping], timestamp: float) -> int:
    """Estimate retention percentage at a given timestamp."""
    for mapping in content_map:
        if mapping.timestamp >= timestamp:
            return int(mapping.retention_percent)
    return 0


# =============================================================================
# Library Video Fallback (Step 8.6)
# =============================================================================


def _extract_duration_from_retention_curve(video_metrics: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Extract video duration from retention curve.

    The retention curve is an array where each element represents retention % at that second.
    The length of the array equals the video duration in seconds.

    Args:
        video_metrics: Dict containing retention_curve from video metrics

    Returns:
        Video duration in seconds, or None if not available
    """
    if not video_metrics:
        return None

    retention_curve = video_metrics.get("retention_curve")
    if retention_curve and isinstance(retention_curve, list) and len(retention_curve) > 0:
        return float(len(retention_curve))

    return None


async def _try_library_match(
    ad_name: str,
    account_id: str,
    access_token: str,
    ad_video_duration: Optional[float] = None,
    duration_tolerance: float = 1.5,
    time_range: Union[str, Dict[str, str]] = "last_30d"
) -> Optional[Dict[str, Any]]:
    """
    Try to find a matching library video for an ad.

    Step 8.6.2: Attempt library video matching when direct video access fails.

    Uses a two-step matching process:
    1. DURATION FILTER (hard requirement): If ad_video_duration is known, only consider
       library videos within ±duration_tolerance seconds. Different duration = different video.
    2. KEYWORD MATCH: Among duration-matched candidates, rank by keyword overlap.

    Args:
        ad_name: Name of the ad (used for keyword matching)
        account_id: Ad account ID
        access_token: Meta API access token
        ad_video_duration: Duration of the ad's video in seconds (if known)
        duration_tolerance: Allowed difference in seconds for duration matching (default ±1.5s)
        time_range: Time range for performance data

    Returns:
        Dict with library_video and match info if found, None otherwise
    """
    try:
        from . import library_video_matcher

        # Fetch library videos
        library_videos = await library_video_matcher.fetch_library_videos(
            account_id, access_token, limit=50
        )

        if not library_videos:
            logger.debug("No library videos found for fallback matching")
            return None

        # STEP 1: Duration filter (hard requirement when duration is known)
        if ad_video_duration is not None and ad_video_duration > 0:
            duration_matched = [
                v for v in library_videos
                if abs(v.duration - ad_video_duration) <= duration_tolerance
            ]
            logger.debug(
                f"Duration filter: {len(duration_matched)}/{len(library_videos)} videos "
                f"match ±{duration_tolerance}s of {ad_video_duration}s"
            )

            if not duration_matched:
                logger.info(
                    f"No library videos match duration {ad_video_duration}s (±{duration_tolerance}s). "
                    f"Library durations: {[v.duration for v in library_videos[:5]]}..."
                )
                return None

            candidates = duration_matched
        else:
            # Duration unknown - fall back to all videos (keyword-only matching)
            logger.debug("Ad video duration unknown, using keyword-only matching")
            candidates = library_videos

        # STEP 2: Keyword matching among candidates
        config = library_video_matcher.MatchingConfig()
        ad_keywords = library_video_matcher.extract_keywords(ad_name, config.name_patterns)

        # If no keywords, but we have duration match, still return best duration match
        if not ad_keywords:
            if ad_video_duration is not None and candidates:
                # Return closest duration match even without keyword match
                closest = min(candidates, key=lambda v: abs(v.duration - ad_video_duration))
                logger.info(
                    f"No keywords extracted, returning closest duration match: "
                    f"{closest.title} ({closest.duration}s)"
                )
                return {
                    "library_video": closest,
                    "matched_keywords": [],
                    "confidence": 0.7,  # Duration-only match
                    "match_method": "duration_only"
                }
            logger.debug(f"No keywords extracted from ad name: {ad_name}")
            return None

        ad_keyword_names = [k[0] for k in ad_keywords]

        # Find best matching library video among candidates
        best_match = None
        best_confidence = 0.0

        for video in candidates:
            video_keywords = library_video_matcher.extract_keywords(video.title, config.name_patterns)
            video_keyword_names = [k[0] for k in video_keywords]

            # Calculate keyword overlap
            shared = set(ad_keyword_names) & set(video_keyword_names)
            if shared:
                keyword_confidence = len(shared) / max(len(ad_keyword_names), len(video_keyword_names))

                # Boost confidence if duration also matches
                if ad_video_duration is not None:
                    duration_diff = abs(video.duration - ad_video_duration)
                    # Perfect duration match (within 0.5s) gets full boost
                    duration_boost = 0.1 if duration_diff <= 0.5 else 0.05
                    confidence = min(keyword_confidence + duration_boost, 1.0)
                else:
                    confidence = keyword_confidence

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "library_video": video,
                        "matched_keywords": list(shared),
                        "confidence": confidence,
                        "match_method": "duration_and_keywords" if ad_video_duration else "keywords_only",
                        "duration_diff": abs(video.duration - ad_video_duration) if ad_video_duration else None
                    }

        if best_match and best_confidence >= config.min_confidence_threshold:
            logger.info(
                f"Library fallback match found: {best_match['library_video'].title} "
                f"(confidence: {best_confidence:.2f}, method: {best_match['match_method']})"
            )
            return best_match

        # If duration matched but no keyword match, return best duration match with lower confidence
        if ad_video_duration is not None and candidates:
            closest = min(candidates, key=lambda v: abs(v.duration - ad_video_duration))
            logger.info(
                f"No keyword match, returning closest duration match: "
                f"{closest.title} ({closest.duration}s)"
            )
            return {
                "library_video": closest,
                "matched_keywords": [],
                "confidence": 0.6,  # Duration-only, no keywords
                "match_method": "duration_only"
            }

        return None

    except Exception as e:
        logger.warning(f"Library match fallback failed: {e}")
        return None


async def _analyze_with_library_fallback(
    library_video: Any,
    match_confidence: float,
    matched_keywords: List[str],
    access_token: str,
    extract_subtitles: bool = False
) -> Dict[str, Any]:
    """
    Analyze a library video as fallback for inaccessible Page-owned video.

    Step 8.6.3: Download and analyze library video content.

    Args:
        library_video: LibraryVideo object from library_video_matcher
        match_confidence: Confidence score of the match
        matched_keywords: Keywords that matched
        access_token: Meta API access token
        extract_subtitles: Whether to run OCR

    Returns:
        Video analysis dict with frames, subtitles, metadata
    """
    from . import video_processing

    analysis = {
        "source": "library_fallback",
        "library_video_id": library_video.id,
        "library_video_title": library_video.title,
        "match_confidence": match_confidence,
        "matched_keywords": matched_keywords,
        "duration_seconds": library_video.duration,
        "frames_extracted": 0,
        "subtitles_detected": []
    }

    # Skip if no source URL
    if not library_video.source_url:
        logger.warning("Library video has no source URL for download")
        return analysis

    try:
        async with video_processing.VideoProcessingContext() as ctx:
            video_path = ctx.get_video_path("library_video.mp4")

            # Download video from source URL
            file_size = await video_processing.download_video_from_url(
                library_video.source_url,
                video_path
            )

            if not file_size or not ctx.temp_dir:
                logger.warning("Failed to download library video")
                return analysis

            # Get metadata via ffprobe
            metadata = await video_processing.get_video_metadata_ffprobe(video_path)

            if metadata:
                analysis["dimensions"] = {
                    "width": metadata.width,
                    "height": metadata.height
                }
                analysis["fps"] = metadata.fps
                analysis["codec"] = metadata.codec

            # Extract frames
            frames = await video_processing.extract_frames(
                video_path,
                ctx.temp_dir,
                video_processing.VideoConfig()
            )

            analysis["frames_extracted"] = len(frames)

            # Run OCR if enabled
            if extract_subtitles and frames:
                subtitles = await video_processing.detect_subtitles_batch(frames[:10])
                analysis["subtitles_detected"] = [
                    {
                        "text": s.text,
                        "timestamp": s.timestamp,
                        "confidence": s.confidence
                    }
                    for s in subtitles
                ]

            logger.info(f"Library fallback analysis complete: {len(frames)} frames extracted")

    except Exception as e:
        logger.warning(f"Library video analysis failed: {e}")
        analysis["error"] = str(e)

    return analysis


def _is_permission_error(error: Exception) -> bool:
    """Check if an error is a video permission error (error code 10)."""
    error_str = str(error).lower()
    return (
        "error code 10" in error_str or
        "permission" in error_str or
        "(#10)" in error_str or
        "unsupported get request" in error_str
    )


@mcp_server.tool()
@meta_api_tool
async def analyze_video_creative(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    include_benchmarks: bool = True,
    extract_frames: bool = False,
    extract_subtitles: bool = False
) -> str:
    """
    Analyze a video ad creative with retention metrics and benchmarks.

    Returns video metadata, retention metrics (play curve, thruplay rate),
    text content, performance metrics, and comparison to account benchmarks.

    Optionally extracts frames and detects subtitles (requires ffmpeg/tesseract).

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)
        include_benchmarks: Whether to include account benchmarks (default: True)
        extract_frames: Whether to extract video frames (requires ffmpeg)
        extract_subtitles: Whether to detect subtitles in frames (requires tesseract)

    Returns:
        JSON with complete video creative analysis
    """
    # Token is resolved by @meta_api_tool decorator
    assert access_token is not None, "access_token required"

    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        # Fetch creative metadata
        ad_data = await _fetch_creative_metadata(ad_id, access_token)

        creative = ad_data.get("creative", {})
        account_id = ad_data.get("account_id", "")

        # Detect creative type
        creative_type, type_data = _detect_creative_type(creative)

        # Check if this is actually a video creative
        if creative_type != CreativeType.VIDEO:
            return json.dumps({
                "error": "This is not a video creative",
                "creative_type": creative_type.value,
                "hint": "Use analyze_image_creative for image ads"
            }, indent=2)

        # Extract content
        content = _extract_creative_content(creative)

        # Get video ID
        video_id = creative.get("video_id")
        if not video_id:
            # Try to get from object_story_spec
            object_story_spec = creative.get("object_story_spec", {})
            video_data = object_story_spec.get("video_data", {})
            video_id = video_data.get("video_id")

        # Initialize result
        analysis_level = AnalysisLevel.METADATA_ONLY.value
        video_analysis = {
            "video_id": video_id,
            "thumbnail_url": creative.get("thumbnail_url"),
            "duration_seconds": None,
            "dimensions": None,
            "frames_extracted": 0,
            "subtitles_detected": []
        }

        # Fetch video metadata if we have video_id
        video_meta_duration = None
        if video_id:
            video_endpoint = f"{video_id}"
            video_params = {"fields": "length,width,height,source"}
            video_meta = await make_api_request(video_endpoint, access_token, video_params)

            if "error" not in video_meta:
                video_meta_duration = float(video_meta.get("length", 0))
                video_analysis["duration_seconds"] = video_meta_duration
                width = video_meta.get("width")
                height = video_meta.get("height")
                if width and height:
                    from math import gcd
                    divisor = gcd(width, height)
                    aspect_ratio = f"{width // divisor}:{height // divisor}"
                    video_analysis["dimensions"] = {
                        "width": width,
                        "height": height,
                        "aspect_ratio": aspect_ratio
                    }
                analysis_level = AnalysisLevel.THUMBNAIL_ONLY.value

        # Fetch video retention metrics EARLY (needed for duration in library fallback)
        video_metrics = await _fetch_video_retention_metrics(ad_id, time_range, access_token)

        # Determine video duration from best available source
        # Priority: video metadata > retention curve length
        ad_video_duration = video_meta_duration
        if not ad_video_duration or ad_video_duration <= 0:
            retention_duration = _extract_duration_from_retention_curve(video_metrics)
            if retention_duration:
                ad_video_duration = retention_duration
                video_analysis["duration_seconds"] = retention_duration
                logger.debug(f"Using duration from retention curve: {retention_duration}s")

        # Optionally process video frames
        library_fallback_used = False
        if extract_frames and video_id and account_id:
            ffmpeg_ok, _ = check_ffmpeg_available()
            if ffmpeg_ok:
                try:
                    processing_result = await process_video(
                        video_id=video_id,
                        account_id=account_id,
                        access_token=access_token,
                        extract_subtitles=extract_subtitles
                    )

                    if processing_result.frames:
                        video_analysis["frames_extracted"] = len(processing_result.frames)
                        analysis_level = AnalysisLevel.FULL.value

                    if processing_result.subtitles:
                        video_analysis["subtitles_detected"] = [
                            {
                                "text": s.text,
                                "timestamp": s.timestamp,
                                "confidence": s.confidence
                            }
                            for s in processing_result.subtitles
                        ]

                except Exception as e:
                    logger.warning(f"Video processing failed: {e}")

                    # Step 8.6.1: Try library fallback on permission errors
                    if _is_permission_error(e):
                        ad_name = ad_data.get("name", "")
                        logger.info(
                            f"Permission error detected, trying library fallback for: {ad_name} "
                            f"(duration: {ad_video_duration}s)"
                        )

                        # Pass video duration for accurate matching
                        match = await _try_library_match(
                            ad_name=ad_name,
                            account_id=account_id,
                            access_token=access_token,
                            ad_video_duration=ad_video_duration,
                            time_range=time_range
                        )

                        if match:
                            library_fallback_used = True
                            fallback_analysis = await _analyze_with_library_fallback(
                                library_video=match["library_video"],
                                match_confidence=match["confidence"],
                                matched_keywords=match["matched_keywords"],
                                access_token=access_token,
                                extract_subtitles=extract_subtitles
                            )

                            # Update video_analysis with fallback data
                            video_analysis["source"] = "library_fallback"
                            video_analysis["library_video_id"] = fallback_analysis.get("library_video_id")
                            video_analysis["library_video_title"] = fallback_analysis.get("library_video_title")
                            video_analysis["match_confidence"] = fallback_analysis.get("match_confidence")
                            video_analysis["matched_keywords"] = fallback_analysis.get("matched_keywords")
                            video_analysis["match_method"] = match.get("match_method", "unknown")
                            video_analysis["frames_extracted"] = fallback_analysis.get("frames_extracted", 0)
                            video_analysis["subtitles_detected"] = fallback_analysis.get("subtitles_detected", [])

                            if fallback_analysis.get("dimensions"):
                                video_analysis["dimensions"] = fallback_analysis["dimensions"]

                            if fallback_analysis.get("frames_extracted", 0) > 0:
                                analysis_level = "library_match"

                            logger.info(
                                f"Library fallback successful: {fallback_analysis.get('library_video_title')} "
                                f"(method: {match.get('match_method')})"
                            )

        # Fetch standard performance metrics
        raw_metrics = await _fetch_performance_metrics(ad_id, time_range, access_token)
        metrics = None
        metrics_dict = None
        if raw_metrics:
            metrics = _parse_performance_metrics(raw_metrics, time_range)
            metrics_dict = asdict(metrics)

        # Fetch benchmarks and compare
        benchmark_comparison = None
        if include_benchmarks and metrics and account_id:
            benchmarks = await _calculate_benchmarks(account_id, time_range, None, access_token)
            if benchmarks:
                benchmark_comparison = _compare_to_benchmarks(metrics, benchmarks)

        # Identify drop-off points
        dropoff_points = []
        if video_metrics and video_metrics.get("retention_percentages"):
            dropoff_points = _identify_dropoff_points(video_metrics["retention_percentages"])

        # Build result
        result = {
            "ad_id": ad_id,
            "ad_name": ad_data.get("name", ""),
            "account_id": account_id,
            "creative_id": creative.get("id", ""),
            "creative_type": creative_type.value,
            "analysis_level": analysis_level,
            "video_analysis": video_analysis,
            "content": {
                "headlines": content.headlines,
                "primary_texts": content.primary_texts,
                "descriptions": content.descriptions,
                "call_to_action": content.call_to_action,
                "link_url": content.link_url
            },
            "performance_metrics": metrics_dict,
            "video_metrics": video_metrics,
            "dropoff_analysis": {
                "significant_dropoffs": dropoff_points,
                "has_early_dropoff": any(d["checkpoint"] == "25%" and d["drop_percent"] > 30 for d in dropoff_points)
            } if dropoff_points else None,
            "benchmark_comparison": benchmark_comparison
        }

        return json.dumps(result, indent=2)

    except CreativeAnalysisError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error analyzing video creative for {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


# =============================================================================
# Unified Analysis Tool (Main Entry Point)
# =============================================================================

@mcp_server.tool()
@meta_api_tool
async def analyze_creative(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    include_benchmarks: bool = True,
    extract_frames: bool = False,
    extract_subtitles: bool = False
) -> str:
    """
    Analyze any ad creative (image or video) with performance metrics.

    Automatically detects creative type and routes to appropriate analysis.
    Returns visual analysis, text content, performance metrics, and benchmarks.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)
        include_benchmarks: Whether to include account benchmarks (default: True)
        extract_frames: For video: whether to extract frames (requires ffmpeg)
        extract_subtitles: For video: whether to detect subtitles (requires tesseract)

    Returns:
        JSON with complete creative analysis (format depends on creative type)
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        # Fetch creative metadata to detect type
        ad_data = await _fetch_creative_metadata(ad_id, access_token)
        creative = ad_data.get("creative", {})

        # Detect creative type
        creative_type, _ = _detect_creative_type(creative)

        # Route to appropriate analysis
        if creative_type == CreativeType.VIDEO:
            return await analyze_video_creative(
                ad_id=ad_id,
                access_token=access_token,
                account_name=account_name,
                time_range=time_range,
                include_benchmarks=include_benchmarks,
                extract_frames=extract_frames,
                extract_subtitles=extract_subtitles
            )
        else:
            # IMAGE, CAROUSEL, or UNKNOWN all use image analysis
            return await analyze_image_creative(
                ad_id=ad_id,
                access_token=access_token,
                account_name=account_name,
                time_range=time_range,
                include_benchmarks=include_benchmarks
            )

    except CreativeAnalysisError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error analyzing creative {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


# =============================================================================
# Batch Analysis Tool
# =============================================================================

@mcp_server.tool()
@meta_api_tool
async def analyze_account_creatives(
    account_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    limit: int = 20,
    min_spend: float = 1.0,
    creative_type_filter: Optional[str] = None
) -> str:
    """
    Analyze multiple creatives from an ad account.

    Fetches ads with spend in the time range and provides summary statistics
    with top/bottom performers identified.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)
        limit: Maximum number of ads to analyze (default: 20)
        min_spend: Minimum spend to include (default: $1.0)
        creative_type_filter: Filter by type: "image", "video", or None for all

    Returns:
        JSON with account creative analysis summary
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    # Ensure account_id has act_ prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    try:
        # Fetch ads with insights
        endpoint = f"{account_id}/ads"
        params = {
            "fields": (
                "id,name,status,"
                "creative{id,name,thumbnail_url,object_story_spec,asset_feed_spec,video_id},"
                "insights.date_preset({date_preset})"
                "{impressions,clicks,ctr,spend,cpc,cpm,reach}"
            ).replace("{date_preset}", time_range if isinstance(time_range, str) else "last_30d"),
            "limit": min(limit * 2, 100),  # Fetch more to filter
            "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE", "PAUSED"]}])
        }

        data = await make_api_request(endpoint, access_token, params)

        if "error" in data:
            return json.dumps({
                "error": f"Failed to fetch ads: {data.get('error')}",
                "error_type": "APIError"
            }, indent=2)

        ads = data.get("data", [])
        if not ads:
            return json.dumps({
                "account_id": account_id,
                "time_range": time_range,
                "total_ads": 0,
                "message": "No ads found in account"
            }, indent=2)

        # Process and filter ads
        processed_ads = []
        type_counts = {"image": 0, "video": 0, "carousel": 0, "unknown": 0}

        for ad in ads:
            # Get insights
            insights = ad.get("insights", {}).get("data", [])
            if not insights:
                continue

            insight = insights[0]
            spend = float(insight.get("spend", 0))

            # Filter by minimum spend
            if spend < min_spend:
                continue

            # Detect creative type
            creative = ad.get("creative", {})
            creative_type, _ = _detect_creative_type(creative)
            type_str = creative_type.value

            # Filter by creative type if specified
            if creative_type_filter and type_str != creative_type_filter:
                continue

            type_counts[type_str] = type_counts.get(type_str, 0) + 1

            # Build ad summary
            processed_ads.append({
                "ad_id": ad.get("id"),
                "ad_name": ad.get("name", ""),
                "creative_type": type_str,
                "thumbnail_url": creative.get("thumbnail_url"),
                "metrics": {
                    "impressions": int(insight.get("impressions", 0)),
                    "clicks": int(insight.get("clicks", 0)),
                    "ctr": float(insight.get("ctr", 0)),
                    "spend": spend,
                    "cpc": float(insight.get("cpc", 0)) if insight.get("cpc") else None,
                    "cpm": float(insight.get("cpm", 0)) if insight.get("cpm") else None
                }
            })

            if len(processed_ads) >= limit:
                break

        if not processed_ads:
            return json.dumps({
                "account_id": account_id,
                "time_range": time_range,
                "total_ads": 0,
                "message": f"No ads found with spend >= ${min_spend}"
            }, indent=2)

        # Sort by CTR for ranking
        sorted_by_ctr = sorted(
            processed_ads,
            key=lambda x: x["metrics"]["ctr"],
            reverse=True
        )

        # Calculate summary statistics
        total_spend = sum(ad["metrics"]["spend"] for ad in processed_ads)
        total_impressions = sum(ad["metrics"]["impressions"] for ad in processed_ads)
        total_clicks = sum(ad["metrics"]["clicks"] for ad in processed_ads)
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        ctrs = [ad["metrics"]["ctr"] for ad in processed_ads if ad["metrics"]["ctr"] > 0]
        avg_ctr_per_ad = sum(ctrs) / len(ctrs) if ctrs else 0

        # Identify top and bottom performers
        top_performers = sorted_by_ctr[:3]
        bottom_performers = sorted_by_ctr[-3:] if len(sorted_by_ctr) > 3 else []

        result = {
            "account_id": account_id,
            "time_range": time_range,
            "summary": {
                "total_ads_analyzed": len(processed_ads),
                "total_spend": round(total_spend, 2),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "overall_ctr": round(avg_ctr, 2),
                "avg_ctr_per_ad": round(avg_ctr_per_ad, 2),
                "creative_type_breakdown": type_counts
            },
            "top_performers": [
                {
                    "ad_id": ad["ad_id"],
                    "ad_name": ad["ad_name"][:50],
                    "creative_type": ad["creative_type"],
                    "ctr": round(ad["metrics"]["ctr"], 2),
                    "spend": round(ad["metrics"]["spend"], 2)
                }
                for ad in top_performers
            ],
            "bottom_performers": [
                {
                    "ad_id": ad["ad_id"],
                    "ad_name": ad["ad_name"][:50],
                    "creative_type": ad["creative_type"],
                    "ctr": round(ad["metrics"]["ctr"], 2),
                    "spend": round(ad["metrics"]["spend"], 2)
                }
                for ad in bottom_performers
            ],
            "all_ads": [
                {
                    "ad_id": ad["ad_id"],
                    "ad_name": ad["ad_name"][:50],
                    "creative_type": ad["creative_type"],
                    "thumbnail_url": ad["thumbnail_url"],
                    "metrics": ad["metrics"]
                }
                for ad in sorted_by_ctr
            ]
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing account creatives for {account_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)


# =============================================================================
# AI Insights Generation
# =============================================================================

def _generate_insights(
    creative_type: str,
    metrics: Optional[Dict[str, Any]],
    video_metrics: Optional[Dict[str, Any]],
    benchmark_comparison: Optional[Dict[str, Any]],
    dropoff_analysis: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate rule-based insights from creative analysis.

    Args:
        creative_type: Type of creative (image/video)
        metrics: Performance metrics dict
        video_metrics: Video-specific metrics (for video creatives)
        benchmark_comparison: Benchmark comparison results
        dropoff_analysis: Video dropoff analysis

    Returns:
        Dict with strengths, weaknesses, and recommendations
    """
    insights = {
        "strengths": [],
        "weaknesses": [],
        "recommendations": []
    }

    if not metrics:
        return insights

    # Analyze benchmark comparison
    if benchmark_comparison:
        # CTR analysis
        if "ctr" in benchmark_comparison:
            ctr_data = benchmark_comparison["ctr"]
            if ctr_data["performance"] == "above":
                insights["strengths"].append(
                    f"CTR is {ctr_data['diff_percent']:+.1f}% above account average"
                )
            elif ctr_data["performance"] == "below":
                insights["weaknesses"].append(
                    f"CTR is {abs(ctr_data['diff_percent']):.1f}% below account average"
                )
                insights["recommendations"].append({
                    "type": "ctr_improvement",
                    "priority": "high",
                    "suggestion": "Test new headlines or visuals to improve click-through rate"
                })

        # CPC analysis
        if "cpc" in benchmark_comparison:
            cpc_data = benchmark_comparison["cpc"]
            if cpc_data["performance"] == "below":  # Lower CPC is better
                insights["strengths"].append(
                    f"CPC is {abs(cpc_data['diff_percent']):.1f}% below account average"
                )
            elif cpc_data["performance"] == "above":
                insights["weaknesses"].append(
                    f"CPC is {cpc_data['diff_percent']:.1f}% above account average"
                )

    # Video-specific insights
    if creative_type == "video" and video_metrics:
        thruplay_rate = video_metrics.get("thruplay_rate", 0)
        watch_completion = video_metrics.get("watch_completion_rate", 0)

        # Thruplay analysis
        if thruplay_rate > 15:
            insights["strengths"].append(f"Strong thruplay rate of {thruplay_rate:.1f}%")
        elif thruplay_rate < 5:
            insights["weaknesses"].append(f"Low thruplay rate of {thruplay_rate:.1f}%")
            insights["recommendations"].append({
                "type": "video_engagement",
                "priority": "high",
                "suggestion": "Consider shorter video or stronger hook in first 3 seconds"
            })

        # Dropoff analysis
        if dropoff_analysis and dropoff_analysis.get("has_early_dropoff"):
            insights["weaknesses"].append("Significant viewer dropoff in first 25% of video")
            insights["recommendations"].append({
                "type": "hook",
                "priority": "high",
                "suggestion": "Lead with the outcome or benefit, not a question. Grab attention immediately."
            })

        # Retention curve insights
        retention = video_metrics.get("retention_percentages", {})
        if retention.get("50%", 0) > 30:
            insights["strengths"].append(f"Good mid-video retention ({retention['50%']:.0f}% at 50%)")

    return insights


@mcp_server.tool()
@meta_api_tool
async def get_creative_insights(
    ad_id: str,
    access_token: Optional[str] = None,
    account_name: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d"
) -> str:
    """
    Generate AI insights for an ad creative.

    Analyzes performance metrics and generates actionable recommendations
    based on benchmark comparisons and retention patterns.

    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional)
        account_name: Account name from credentials.json (optional)
        time_range: Time range for metrics (default: last_30d)

    Returns:
        JSON with strengths, weaknesses, and recommendations
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    try:
        # Get full analysis first
        analysis_result = await analyze_creative(
            ad_id=ad_id,
            access_token=access_token,
            account_name=account_name,
            time_range=time_range,
            include_benchmarks=True
        )

        analysis = json.loads(analysis_result)

        if "error" in analysis:
            return analysis_result

        # Generate insights
        insights = _generate_insights(
            creative_type=analysis.get("creative_type", "unknown"),
            metrics=analysis.get("performance_metrics"),
            video_metrics=analysis.get("video_metrics"),
            benchmark_comparison=analysis.get("benchmark_comparison"),
            dropoff_analysis=analysis.get("dropoff_analysis")
        )

        result = {
            "ad_id": ad_id,
            "ad_name": analysis.get("ad_name", ""),
            "creative_type": analysis.get("creative_type"),
            "insights": insights,
            "summary": {
                "total_strengths": len(insights["strengths"]),
                "total_weaknesses": len(insights["weaknesses"]),
                "total_recommendations": len(insights["recommendations"]),
                "priority_actions": [
                    r for r in insights["recommendations"]
                    if r.get("priority") == "high"
                ]
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error generating insights for {ad_id}: {e}")
        return json.dumps({
            "error": str(e),
            "error_type": "UnexpectedError"
        }, indent=2)
