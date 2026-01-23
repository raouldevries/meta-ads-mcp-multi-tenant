"""Creative Analysis functionality for Meta Ads API.

This module provides tools for analyzing ad creatives (images and videos),
combining visual analysis with performance metrics to generate insights.
"""

import json
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .api import meta_api_tool, make_api_request
from .utils import logger
from .server import mcp_server


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


# =============================================================================
# MCP Tools (Stubs for now - will be implemented in later steps)
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
