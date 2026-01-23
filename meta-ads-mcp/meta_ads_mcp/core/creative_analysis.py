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
        if video_id:
            video_endpoint = f"{video_id}"
            video_params = {"fields": "length,width,height,source"}
            video_meta = await make_api_request(video_endpoint, access_token, video_params)

            if "error" not in video_meta:
                video_analysis["duration_seconds"] = float(video_meta.get("length", 0))
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

        # Optionally process video frames
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

        # Fetch video retention metrics
        video_metrics = await _fetch_video_retention_metrics(ad_id, time_range, access_token)

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
