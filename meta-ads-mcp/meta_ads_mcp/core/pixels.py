"""Pixel management functionality for Meta Ads API.

This module provides read-only tools for viewing Meta Pixels, conversion events,
and offline conversion data. These features use the existing ads_read permission.
"""

import json
from typing import Optional
from .api import meta_api_tool, make_api_request
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_pixels(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Get Meta Pixels associated with an ad account.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        limit: Maximum number of pixels to return (default: 25)

    Returns:
        JSON response with pixels including id, name, code, and last_fired_time.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    endpoint = f"{account_id}/adspixels"
    params = {
        "fields": "id,name,code,creation_time,last_fired_time,is_unavailable,is_created_by_business,owner_business,owner_ad_account,data_use_setting,enable_automatic_matching,first_party_cookie_status,automatic_matching_fields",
        "limit": limit
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_pixel_details(
    pixel_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific Meta Pixel.

    Args:
        pixel_id: Meta Pixel ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with full pixel details including configuration and stats.
    """
    if not pixel_id:
        return json.dumps({"error": "No pixel ID provided"}, indent=2)

    endpoint = f"{pixel_id}"
    params = {
        "fields": "id,name,code,creation_time,last_fired_time,is_unavailable,is_created_by_business,owner_business,owner_ad_account,data_use_setting,enable_automatic_matching,first_party_cookie_status,automatic_matching_fields,matched_entries_count,duplicate_entries_count"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_pixel_stats(
    pixel_id: str,
    access_token: Optional[str] = None,
    aggregation: str = "event",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> str:
    """
    Get statistics for a Meta Pixel including event counts.

    Args:
        pixel_id: Meta Pixel ID
        access_token: Meta API access token (optional)
        aggregation: How to aggregate stats. Values: "event", "device", "browser_type"
        start_time: Start time in ISO 8601 format (optional)
        end_time: End time in ISO 8601 format (optional)

    Returns:
        JSON response with pixel statistics by event type.
    """
    if not pixel_id:
        return json.dumps({"error": "No pixel ID provided"}, indent=2)

    endpoint = f"{pixel_id}/stats"
    params = {
        "aggregation": aggregation
    }

    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_pixel_events(
    pixel_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get the list of events being tracked by a Meta Pixel.

    Args:
        pixel_id: Meta Pixel ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with event types being tracked.
    """
    if not pixel_id:
        return json.dumps({"error": "No pixel ID provided"}, indent=2)

    endpoint = f"{pixel_id}/stats"
    params = {
        "aggregation": "event"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_pixel_code(
    pixel_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get the JavaScript code snippet for a Meta Pixel.

    Args:
        pixel_id: Meta Pixel ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with the pixel base code and installation instructions.
    """
    if not pixel_id:
        return json.dumps({"error": "No pixel ID provided"}, indent=2)

    endpoint = f"{pixel_id}"
    params = {
        "fields": "id,name,code"
    }

    data = await make_api_request(endpoint, access_token, params)

    # Add installation instructions
    if "code" in data:
        data["installation_instructions"] = {
            "step_1": "Add the pixel base code to the <head> section of every page",
            "step_2": "Add event tracking code after the base code for specific actions",
            "standard_events": [
                "PageView", "ViewContent", "Search", "AddToCart",
                "AddToWishlist", "InitiateCheckout", "AddPaymentInfo",
                "Purchase", "Lead", "CompleteRegistration"
            ],
            "example_event": "fbq('track', 'Purchase', {value: 10.00, currency: 'USD'});"
        }

    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_offline_conversion_data_sets(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Get offline conversion data sets for an ad account.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        limit: Maximum number of data sets to return (default: 25)

    Returns:
        JSON response with offline conversion data sets.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    endpoint = f"{account_id}/offline_conversion_data_sets"
    params = {
        "fields": "id,name,description,enable_auto_assign_to_accounts,auto_assign_to_new_accounts_only,is_mta_use_enabled,usage,data_origin,creation_time,last_upload_app,last_upload_app_changed_time,duplicate_entries,valid_entries,matched_entries,event_stats,event_time_min,event_time_max,upload_rate,attribute_stats",
        "limit": limit
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_custom_conversions(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Get custom conversions for an ad account.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        limit: Maximum number of custom conversions to return (default: 25)

    Returns:
        JSON response with custom conversions including rules and pixel associations.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    endpoint = f"{account_id}/customconversions"
    params = {
        "fields": "id,name,description,account_id,pixel,rule,default_conversion_value,is_archived,is_unavailable,retention_days,event_source_type,aggregation_rule,last_fired_time,creation_time,first_fired_time,data_sources,custom_event_type",
        "limit": limit
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_custom_conversion_details(
    custom_conversion_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific custom conversion.

    Args:
        custom_conversion_id: Custom conversion ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with full custom conversion details.
    """
    if not custom_conversion_id:
        return json.dumps({"error": "No custom conversion ID provided"}, indent=2)

    endpoint = f"{custom_conversion_id}"
    params = {
        "fields": "id,name,description,account_id,pixel,rule,default_conversion_value,is_archived,is_unavailable,retention_days,event_source_type,aggregation_rule,last_fired_time,creation_time,first_fired_time,data_sources,custom_event_type"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)
