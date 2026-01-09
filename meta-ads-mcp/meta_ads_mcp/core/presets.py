"""
Field presets and defaults for Meta Ads API requests.

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
    "claude_desktop": 25,
    "claude_code": 100,
    "api_max": 500
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
