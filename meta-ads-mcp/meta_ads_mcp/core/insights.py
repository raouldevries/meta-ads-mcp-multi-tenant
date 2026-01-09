"""Insights and Reporting functionality for Meta Ads API."""

import json
from typing import Optional, Union, Dict, List
from .api import meta_api_tool, make_api_request
from .presets import get_insight_fields
from .server import mcp_server


# Comprehensive list of available insight fields
INSIGHT_FIELDS = [
    # Identification
    "account_id", "account_name", "campaign_id", "campaign_name",
    "adset_id", "adset_name", "ad_id", "ad_name",

    # Date Range (always included in API response)
    "date_start", "date_stop",

    # Core Metrics
    "impressions", "clicks", "spend", "reach", "frequency",

    # Click Metrics
    "cpc", "cpm", "cpp", "ctr",
    "unique_clicks", "unique_ctr", "cost_per_unique_click",
    "inline_link_clicks", "inline_link_click_ctr",
    "outbound_clicks", "outbound_clicks_ctr",

    # Action Metrics
    "actions", "action_values", "conversions", "conversion_values",
    "cost_per_action_type", "cost_per_conversion",

    # Video Metrics
    "video_p25_watched_actions", "video_p50_watched_actions",
    "video_p75_watched_actions", "video_p100_watched_actions",
    "video_thruplay_watched_actions", "video_avg_time_watched_actions",
    "video_play_actions",

    # Engagement Metrics
    "social_spend", "estimated_ad_recall_rate", "estimated_ad_recallers",

    # Quality Metrics
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking",

    # Purchase/ROAS Metrics
    "purchase_roas", "website_purchase_roas",
]


@mcp_server.tool()
@meta_api_tool
async def get_insights(
    object_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    breakdown: str = "",
    action_breakdowns: Optional[List[str]] = None,
    level: str = "ad",
    limit: int = 25,
    after: str = "",
    field_preset: str = "",
    action_attribution_windows: Optional[List[str]] = None,
    time_increment: Optional[str] = None,
    filtering: Optional[List[Dict]] = None,
    sort: Optional[List[str]] = None,
    use_unified_attribution_setting: bool = True,
    fields: Optional[List[str]] = None
) -> str:
    """
    Get performance insights for a campaign, ad set, ad or account.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        access_token: Meta API access token (optional - will use cached token if not provided)
        time_range: Either a preset time range string or a dictionary with "since" and "until" dates in YYYY-MM-DD format
                   Preset options: today, yesterday, this_month, last_month, this_quarter, maximum, data_maximum,
                   last_3d, last_7d, last_14d, last_28d, last_30d, last_90d, last_week_mon_sun,
                   last_week_sun_sat, last_quarter, last_year, this_week_mon_today, this_week_sun_today, this_year
                   Dictionary example: {"since":"2023-01-01","until":"2023-01-31"}
        breakdown: Optional breakdown dimension. Valid values include:
                   Demographic: age, gender, country, region, dma
                   Platform/Device: device_platform, platform_position, publisher_platform, impression_device
                   Creative Assets: ad_format_asset, body_asset, call_to_action_asset, description_asset,
                                  image_asset, link_url_asset, title_asset, video_asset
                   Time-based: hourly_stats_aggregated_by_advertiser_time_zone,
                              hourly_stats_aggregated_by_audience_time_zone, frequency_value
                   Other: product_id, place_page_id
        action_breakdowns: Optional list of action breakdowns. Valid values:
                          action_device, action_type, action_target_id, action_destination,
                          action_reaction, action_carousel_card_id, action_carousel_card_name,
                          action_video_sound, action_video_type, conversion_destination,
                          standard_event_content_type, signal_source_bucket
        level: Level of aggregation (ad, adset, campaign, account)
        limit: Maximum number of results to return per page (default: 25)
        after: Pagination cursor to get the next set of results
        field_preset: Optional preset for fields (basic, efficiency, conversions, video, full)
        action_attribution_windows: Optional list of attribution windows (e.g., ["1d_click", "7d_click", "1d_view"])
        time_increment: Time increment for results. Values:
                       "1" - daily, "7" - weekly, "monthly" - monthly,
                       "all_days" - aggregate over entire period
        filtering: Optional list of filters for ad objects. Example:
                  [{"field": "ad.effective_status", "operator": "IN", "value": ["ACTIVE"]}]
                  Operators: EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, IN, NOT_IN, CONTAIN, NOT_CONTAIN
        sort: Optional list of sort fields. Example: ["reach_descending", "impressions_ascending"]
        use_unified_attribution_setting: Use ad set level attribution settings (default: True, matches Ads Manager)
        fields: Optional custom list of fields to retrieve. If not provided, uses comprehensive default list.

    Returns:
        JSON response with insights data including metrics, actions, and pagination info.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    if fields:
        fields_str = ",".join(fields)
    else:
        preset_name = field_preset if field_preset else "efficiency"
        fields_str = get_insight_fields(preset_name)

    params = {
        "fields": fields_str,
        "level": level,
        "limit": limit,
        "use_unified_attribution_setting": "true" if use_unified_attribution_setting else "false"
    }

    # Handle time range based on type
    if isinstance(time_range, dict):
        if "since" in time_range and "until" in time_range:
            params["time_range"] = json.dumps(time_range)
        else:
            return json.dumps({"error": "Custom time_range must contain both 'since' and 'until' keys in YYYY-MM-DD format"}, indent=2)
    else:
        params["date_preset"] = time_range

    if breakdown:
        params["breakdowns"] = breakdown

    if action_breakdowns:
        params["action_breakdowns"] = ",".join(action_breakdowns)

    if after:
        params["after"] = after

    if action_attribution_windows:
        params["action_attribution_windows"] = json.dumps(action_attribution_windows)

    if time_increment:
        params["time_increment"] = time_increment

    if filtering:
        params["filtering"] = json.dumps(filtering)

    if sort:
        params["sort"] = json.dumps(sort)

    data = await make_api_request(endpoint, access_token, params)

    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_insights_by_time(
    object_id: str,
    time_increment: str = "1",
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    breakdown: str = "",
    level: str = "ad",
    limit: int = 100
) -> str:
    """
    Get insights broken down by time period (daily, weekly, or monthly).

    Args:
        object_id: ID of the campaign, ad set, ad or account
        time_increment: Time increment for results:
                       "1" - daily breakdown
                       "7" - weekly breakdown
                       "monthly" - monthly breakdown
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range (default: last_30d)
        breakdown: Optional additional breakdown (e.g., "age", "gender")
        level: Level of aggregation (ad, adset, campaign, account)
        limit: Maximum results per page (default: 100)

    Returns:
        JSON response with time-series insights data.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    params = {
        "fields": "account_id,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,reach,frequency,cpc,cpm,ctr,actions,conversions",
        "level": level,
        "limit": limit,
        "time_increment": time_increment
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    if breakdown:
        params["breakdowns"] = breakdown

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_async_job_status(
    report_run_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Check the status of an asynchronous insights report job.

    Args:
        report_run_id: The ID of the ad report run (from a previous async job creation)
        access_token: Meta API access token (optional)

    Returns:
        JSON response with job status including:
        - async_status: Job Not Started, Job Started, Job Running, Job Completed, Job Failed, Job Skipped
        - async_percent_completion: 0-100
        - time_completed: timestamp when job finished

    Note:
        Report run IDs expire after 30 days.
    """
    if not report_run_id:
        return json.dumps({"error": "No report run ID provided"}, indent=2)

    endpoint = f"{report_run_id}"
    params = {
        "fields": "id,account_id,async_status,async_percent_completion,time_ref,time_completed,date_start,date_stop"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_async_job_results(
    report_run_id: str,
    access_token: Optional[str] = None,
    limit: int = 100,
    after: str = ""
) -> str:
    """
    Get results from a completed asynchronous insights report job.

    Args:
        report_run_id: The ID of the completed ad report run
        access_token: Meta API access token (optional)
        limit: Maximum results per page (default: 100)
        after: Pagination cursor for next page

    Returns:
        JSON response with insights data from the async job.

    Note:
        Only call this after async_status is "Job Completed" and async_percent_completion is 100.
    """
    if not report_run_id:
        return json.dumps({"error": "No report run ID provided"}, indent=2)

    endpoint = f"{report_run_id}/insights"
    params = {
        "limit": limit
    }

    if after:
        params["after"] = after

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_insights_with_actions(
    object_id: str,
    action_breakdowns: Optional[List[str]] = None,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "ad",
    limit: int = 25
) -> str:
    """
    Get insights with detailed action breakdowns.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        action_breakdowns: List of action breakdowns. Options:
                          - action_type: Type of action (link_click, purchase, etc.)
                          - action_device: Device where conversion occurred
                          - action_destination: Where users went after clicking
                          - action_reaction: Reaction type (like, love, etc.)
                          - action_carousel_card_id/name: Which carousel card was clicked
                          - action_video_sound: Video played with sound on/off
                          - action_video_type: Type of video view
                          - conversion_destination: On/off Facebook conversion
                          - standard_event_content_type: Content type for standard events
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range
        level: Level of aggregation
        limit: Maximum results per page

    Returns:
        JSON response with insights including action breakdowns in the actions field.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    if not action_breakdowns:
        action_breakdowns = ["action_type"]

    endpoint = f"{object_id}/insights"

    params = {
        "fields": "account_id,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,actions,action_values,cost_per_action_type,conversions,conversion_values",
        "level": level,
        "limit": limit,
        "action_breakdowns": ",".join(action_breakdowns)
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


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
    if entity_type not in {"campaign", "adset", "ad"}:
        return json.dumps({"error": "entity_type must be campaign, adset, or ad"}, indent=2)

    if not entity_ids:
        return json.dumps({"error": "No entity IDs provided"}, indent=2)

    if len(entity_ids) > 10:
        return json.dumps({
            "error": "Maximum 10 entities can be compared at once",
            "provided": len(entity_ids)
        }, indent=2)

    if not metrics:
        metrics = [
            "spend", "impressions", "reach", "clicks",
            "ctr", "cpc", "cpm", "frequency"
        ]

    results = []
    name_key = f"{entity_type}_name"

    for entity_id in entity_ids:
        try:
            insight_result = await get_insights(
                object_id=entity_id,
                time_range=time_range,
                level=entity_type,
                limit=1,
                access_token=access_token
            )
            insight_data = json.loads(insight_result)
            if "error" in insight_data:
                error_data = insight_data["error"]
                error_message = error_data.get("message", "Unknown error") if isinstance(error_data, dict) else str(error_data)
                results.append({
                    "id": entity_id,
                    "name": entity_id,
                    "error": error_message
                })
                continue

            data = insight_data.get("data", [])
            if not data:
                results.append({
                    "id": entity_id,
                    "name": entity_id,
                    "error": "No data available"
                })
                continue

            entity_data = data[0]
            results.append({
                "id": entity_id,
                "name": entity_data.get(name_key, entity_id),
                "metrics": {metric: entity_data.get(metric, "N/A") for metric in metrics}
            })

        except Exception as error:
            results.append({
                "id": entity_id,
                "error": str(error)
            })

    def parse_metric_value(value: Optional[object]) -> Optional[float]:
        if value in (None, "N/A"):
            return None
        try:
            return float(str(value).replace(",", ""))
        except (ValueError, TypeError):
            return None

    rankings = {}
    for metric in metrics:
        values = []
        for result in results:
            metric_value = parse_metric_value(result.get("metrics", {}).get(metric))
            if metric_value is not None:
                values.append((result["id"], metric_value))

        if values:
            reverse = metric not in ["cpc", "cpm", "frequency"]
            sorted_values = sorted(values, key=lambda item: item[1], reverse=reverse)
            rankings[metric] = {
                "best": sorted_values[0][0],
                "worst": sorted_values[-1][0],
                "ranking": [item[0] for item in sorted_values]
            }

    averages = {}
    for metric in metrics:
        values = []
        for result in results:
            metric_value = parse_metric_value(result.get("metrics", {}).get(metric))
            if metric_value is not None:
                values.append(metric_value)
        if values:
            averages[metric] = sum(values) / len(values)

    for result in results:
        if "metrics" not in result:
            continue
        result["delta_from_avg"] = {}
        for metric in metrics:
            metric_value = parse_metric_value(result["metrics"].get(metric))
            average_value = averages.get(metric)
            if metric_value is None or average_value in (None, 0):
                continue
            delta_pct = ((metric_value - average_value) / average_value) * 100
            result["delta_from_avg"][metric] = f"{delta_pct:+.1f}%"

    return json.dumps({
        "comparison": {
            "entity_type": entity_type,
            "time_range": time_range,
            "metrics": metrics,
            "entity_count": len(results)
        },
        "entities": results,
        "rankings": rankings,
        "averages": {key: round(value, 2) for key, value in averages.items()}
    }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_deleted_archived_insights(
    account_id: str,
    status: str = "ARCHIVED",
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "maximum",
    level: str = "ad",
    limit: int = 50
) -> str:
    """
    Get insights for deleted or archived ad objects.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        status: Status filter - "ARCHIVED" or "DELETED"
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range (default: maximum for lifetime)
        level: Level to retrieve (ad, adset, campaign)
        limit: Maximum results per page

    Returns:
        JSON response with insights for archived/deleted objects.

    Note:
        Deleted/archived objects still have stats that contribute to parent totals.
        Use this to get their individual breakdown.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    if status not in ["ARCHIVED", "DELETED"]:
        return json.dumps({"error": "Status must be 'ARCHIVED' or 'DELETED'"}, indent=2)

    endpoint = f"{account_id}/insights"

    params = {
        "fields": "account_id,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,reach,actions",
        "level": level,
        "limit": limit,
        "filtering": json.dumps([{
            "field": f"{level}.effective_status",
            "operator": "IN",
            "value": [status]
        }])
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_video_insights(
    object_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "ad",
    limit: int = 25
) -> str:
    """
    Get video-specific performance insights.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range
        level: Level of aggregation
        limit: Maximum results per page

    Returns:
        JSON response with video metrics including watch percentages and thruplay.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    video_fields = [
        "account_id", "campaign_id", "campaign_name", "adset_id", "adset_name", "ad_id", "ad_name",
        "impressions", "reach", "spend",
        "video_play_actions",
        "video_p25_watched_actions",
        "video_p50_watched_actions",
        "video_p75_watched_actions",
        "video_p95_watched_actions",
        "video_p100_watched_actions",
        "video_thruplay_watched_actions",
        "video_avg_time_watched_actions",
        "video_play_curve_actions"
    ]

    params = {
        "fields": ",".join(video_fields),
        "level": level,
        "limit": limit
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_demographic_insights(
    object_id: str,
    demographic_breakdown: str = "age,gender",
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "account",
    limit: int = 100
) -> str:
    """
    Get insights broken down by demographic dimensions.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        demographic_breakdown: Breakdown dimensions. Options:
                              "age" - Age ranges (18-24, 25-34, etc.)
                              "gender" - Male, Female, Unknown
                              "age,gender" - Both combined
                              "country" - Country breakdown
                              "region" - Region/state breakdown
                              "dma" - Designated Market Area (US only)
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range
        level: Level of aggregation
        limit: Maximum results per page

    Returns:
        JSON response with insights broken down by demographics.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    params = {
        "fields": "account_id,campaign_id,adset_id,ad_id,impressions,clicks,spend,reach,frequency,actions,ctr,cpc",
        "breakdowns": demographic_breakdown,
        "level": level,
        "limit": limit
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_placement_insights(
    object_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "account",
    limit: int = 100
) -> str:
    """
    Get insights broken down by ad placement (Facebook Feed, Instagram Stories, etc.).

    Args:
        object_id: ID of the campaign, ad set, ad or account
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range
        level: Level of aggregation
        limit: Maximum results per page

    Returns:
        JSON response with insights broken down by publisher_platform and platform_position.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    params = {
        "fields": "account_id,campaign_id,adset_id,ad_id,impressions,clicks,spend,reach,actions,ctr,cpc,cpm",
        "breakdowns": "publisher_platform,platform_position",
        "level": level,
        "limit": limit
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_device_insights(
    object_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    level: str = "account",
    limit: int = 100
) -> str:
    """
    Get insights broken down by device type.

    Args:
        object_id: ID of the campaign, ad set, ad or account
        access_token: Meta API access token (optional)
        time_range: Date preset or custom range
        level: Level of aggregation
        limit: Maximum results per page

    Returns:
        JSON response with insights broken down by device_platform and impression_device.
    """
    if not object_id:
        return json.dumps({"error": "No object ID provided"}, indent=2)

    endpoint = f"{object_id}/insights"

    params = {
        "fields": "account_id,campaign_id,adset_id,ad_id,impressions,clicks,spend,reach,actions,ctr,cpc",
        "breakdowns": "device_platform,impression_device",
        "level": level,
        "limit": limit
    }

    if isinstance(time_range, dict):
        params["time_range"] = json.dumps(time_range)
    else:
        params["date_preset"] = time_range

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)
