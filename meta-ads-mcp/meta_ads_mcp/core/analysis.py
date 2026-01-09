"""Analysis tools for Meta Ads - optimized for large dataset analysis with Claude."""

import json
from typing import Optional, List, Dict, Any, Union
from .api import meta_api_tool, make_api_request
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_active_ads_analysis(
    account_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    performance_metric: str = "ctr",
    top_count: int = 5,
    bottom_count: int = 5,
    middle_count: int = 5,
    include_creative_details: bool = True,
    min_impressions: int = 100,
    min_spend: float = 1.0
) -> str:
    """
    Get analysis of active ads with spend, segmented by performance.

    This tool is optimized for Claude's context window by:
    - Only fetching ads that had spend in the selected period
    - Segmenting into top/middle/bottom performers
    - Optionally enriching with creative details only for relevant ads

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        time_range: Time range preset or custom {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
                   Presets: today, yesterday, last_7d, last_14d, last_30d, last_90d, this_month, last_month
        performance_metric: Metric to rank ads by. Options:
                           - "ctr" (click-through rate) - higher is better
                           - "cpc" (cost per click) - lower is better
                           - "cpm" (cost per 1000 impressions) - lower is better
                           - "spend" (total spend) - for budget analysis
                           - "roas" (return on ad spend) - higher is better (requires conversion tracking)
        top_count: Number of top performers to include (default: 5)
        bottom_count: Number of bottom performers to include (default: 5)
        middle_count: Number of middle performers to include (default: 5)
        include_creative_details: Whether to fetch creative details for segmented ads (default: True)
        min_impressions: Minimum impressions to be included in analysis (default: 100)
        min_spend: Minimum spend (in account currency) to be included (default: 1.0)

    Returns:
        JSON with performance segments: top_performers, middle_performers, bottom_performers,
        plus summary statistics and optionally creative details.
    """
    if not account_id:
        return json.dumps({"error": "No account ID specified"}, indent=2)

    # Build time_range parameter
    if isinstance(time_range, str):
        time_range_param = time_range
    else:
        time_range_param = time_range

    # Step 1: Fetch insights for all ads with activity in the period
    insights_endpoint = f"{account_id}/insights"
    insights_params = {
        "level": "ad",
        "fields": "ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,actions,action_values,purchase_roas",
        "limit": 500  # High limit to get all active ads
    }

    # Handle time_range
    if isinstance(time_range_param, dict):
        insights_params["time_range"] = json.dumps(time_range_param)
    else:
        insights_params["date_preset"] = time_range_param

    insights_data = await make_api_request(insights_endpoint, access_token, insights_params)

    if "error" in insights_data:
        return json.dumps(insights_data, indent=2)

    ads_data = insights_data.get("data", [])

    if not ads_data:
        return json.dumps({
            "message": "No ads with spend found in the selected period",
            "time_range": time_range,
            "account_id": account_id
        }, indent=2)

    # Step 2: Filter ads by minimum thresholds
    filtered_ads = []
    for ad in ads_data:
        spend = float(ad.get("spend", 0))
        impressions = int(ad.get("impressions", 0))

        if spend >= min_spend and impressions >= min_impressions:
            # Parse metrics
            ad["_spend"] = spend
            ad["_impressions"] = impressions
            ad["_clicks"] = int(ad.get("clicks", 0))
            ad["_ctr"] = float(ad.get("ctr", 0))
            ad["_cpc"] = float(ad.get("cpc", 0)) if ad.get("cpc") else None
            ad["_cpm"] = float(ad.get("cpm", 0)) if ad.get("cpm") else None

            # Extract ROAS if available
            roas = None
            if ad.get("purchase_roas"):
                roas_data = ad["purchase_roas"]
                if isinstance(roas_data, list) and len(roas_data) > 0:
                    roas = float(roas_data[0].get("value", 0))
            ad["_roas"] = roas

            filtered_ads.append(ad)

    if not filtered_ads:
        return json.dumps({
            "message": f"No ads met the minimum thresholds (impressions >= {min_impressions}, spend >= {min_spend})",
            "total_ads_found": len(ads_data),
            "time_range": time_range,
            "account_id": account_id
        }, indent=2)

    # Step 3: Sort by performance metric
    metric_key = f"_{performance_metric}"
    reverse_sort = performance_metric in ["ctr", "roas", "spend"]  # Higher is better for these

    # Handle None values in sorting
    def sort_key(ad):
        value = ad.get(metric_key)
        if value is None:
            return float('-inf') if reverse_sort else float('inf')
        return value

    sorted_ads = sorted(filtered_ads, key=sort_key, reverse=reverse_sort)

    # Step 4: Segment into top/middle/bottom
    total_ads = len(sorted_ads)

    top_performers = sorted_ads[:top_count]
    bottom_performers = sorted_ads[-bottom_count:] if bottom_count > 0 else []

    # Middle performers: from the middle of the list
    if middle_count > 0 and total_ads > (top_count + bottom_count):
        middle_start = total_ads // 2 - middle_count // 2
        middle_end = middle_start + middle_count
        middle_performers = sorted_ads[middle_start:middle_end]
    else:
        middle_performers = []

    # Step 5: Clean up internal fields and prepare output
    def clean_ad(ad):
        return {
            "ad_id": ad.get("ad_id"),
            "ad_name": ad.get("ad_name"),
            "adset_name": ad.get("adset_name"),
            "campaign_name": ad.get("campaign_name"),
            "spend": ad.get("spend"),
            "impressions": ad.get("impressions"),
            "clicks": ad.get("clicks"),
            "ctr": ad.get("ctr"),
            "cpc": ad.get("cpc"),
            "cpm": ad.get("cpm"),
            "roas": ad.get("_roas"),
            "actions": ad.get("actions"),
        }

    result = {
        "summary": {
            "account_id": account_id,
            "time_range": time_range,
            "performance_metric": performance_metric,
            "total_ads_with_spend": total_ads,
            "total_spend": sum(ad["_spend"] for ad in filtered_ads),
            "total_impressions": sum(ad["_impressions"] for ad in filtered_ads),
            "total_clicks": sum(ad["_clicks"] for ad in filtered_ads),
            "filters_applied": {
                "min_impressions": min_impressions,
                "min_spend": min_spend
            }
        },
        "top_performers": [clean_ad(ad) for ad in top_performers],
        "middle_performers": [clean_ad(ad) for ad in middle_performers],
        "bottom_performers": [clean_ad(ad) for ad in bottom_performers],
    }

    # Step 6: Optionally fetch creative details for segmented ads
    if include_creative_details:
        # Collect unique ad IDs from all segments
        segment_ad_ids = set()
        for ad in top_performers + middle_performers + bottom_performers:
            segment_ad_ids.add(ad.get("ad_id"))

        if segment_ad_ids:
            creative_details = {}
            for ad_id in segment_ad_ids:
                ad_endpoint = f"{ad_id}"
                ad_params = {
                    "fields": "id,name,creative{id,name,title,body,image_url,thumbnail_url,object_story_spec,asset_feed_spec}"
                }
                ad_data = await make_api_request(ad_endpoint, access_token, ad_params)

                if "error" not in ad_data:
                    creative = ad_data.get("creative", {})
                    creative_details[ad_id] = {
                        "creative_id": creative.get("id"),
                        "creative_name": creative.get("name"),
                        "title": creative.get("title"),
                        "body": creative.get("body"),
                        "image_url": creative.get("image_url") or creative.get("thumbnail_url"),
                    }

                    # Extract from object_story_spec if available
                    oss = creative.get("object_story_spec", {})
                    if oss:
                        link_data = oss.get("link_data", {})
                        if link_data:
                            creative_details[ad_id]["message"] = link_data.get("message")
                            creative_details[ad_id]["link"] = link_data.get("link")
                            creative_details[ad_id]["call_to_action"] = link_data.get("call_to_action", {}).get("type")

            result["creative_details"] = creative_details

    return json.dumps(result, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_campaign_performance_summary(
    account_id: str,
    access_token: Optional[str] = None,
    time_range: Union[str, Dict[str, str]] = "last_30d",
    include_adset_breakdown: bool = False
) -> str:
    """
    Get a summary of campaign performance, showing only campaigns with spend.

    Optimized for context window - returns aggregated metrics per campaign,
    not individual ad data.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        time_range: Time range preset or custom range
        include_adset_breakdown: Include ad set level breakdown (increases response size)

    Returns:
        JSON with campaign-level performance summary
    """
    if not account_id:
        return json.dumps({"error": "No account ID specified"}, indent=2)

    # Fetch campaign-level insights
    insights_endpoint = f"{account_id}/insights"
    insights_params = {
        "level": "campaign",
        "fields": "campaign_id,campaign_name,objective,spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,actions,cost_per_action_type,purchase_roas",
        "limit": 100
    }

    if isinstance(time_range, dict):
        insights_params["time_range"] = json.dumps(time_range)
    else:
        insights_params["date_preset"] = time_range

    insights_data = await make_api_request(insights_endpoint, access_token, insights_params)

    if "error" in insights_data:
        return json.dumps(insights_data, indent=2)

    campaigns = insights_data.get("data", [])

    # Filter to campaigns with spend
    active_campaigns = [c for c in campaigns if float(c.get("spend", 0)) > 0]

    # Sort by spend descending
    active_campaigns.sort(key=lambda x: float(x.get("spend", 0)), reverse=True)

    result = {
        "summary": {
            "account_id": account_id,
            "time_range": time_range,
            "total_campaigns_with_spend": len(active_campaigns),
            "total_spend": sum(float(c.get("spend", 0)) for c in active_campaigns),
            "total_impressions": sum(int(c.get("impressions", 0)) for c in active_campaigns),
            "total_clicks": sum(int(c.get("clicks", 0)) for c in active_campaigns),
        },
        "campaigns": active_campaigns
    }

    # Optionally add ad set breakdown
    if include_adset_breakdown:
        adset_endpoint = f"{account_id}/insights"
        adset_params = {
            "level": "adset",
            "fields": "adset_id,adset_name,campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc",
            "limit": 200
        }

        if isinstance(time_range, dict):
            adset_params["time_range"] = json.dumps(time_range)
        else:
            adset_params["date_preset"] = time_range

        adset_data = await make_api_request(adset_endpoint, access_token, adset_params)

        if "error" not in adset_data:
            adsets = adset_data.get("data", [])
            active_adsets = [a for a in adsets if float(a.get("spend", 0)) > 0]
            result["adsets"] = active_adsets

    return json.dumps(result, indent=2)
