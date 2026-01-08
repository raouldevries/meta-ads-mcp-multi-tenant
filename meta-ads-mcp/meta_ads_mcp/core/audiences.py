"""Audience management functionality for Meta Ads API.

This module provides read-only tools for viewing Custom Audiences and Saved Audiences.
These features use the existing ads_read permission.
"""

import json
from typing import Optional
from .api import meta_api_tool, make_api_request
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_custom_audiences(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 25,
    filter_by_subtype: Optional[str] = None
) -> str:
    """
    Get custom audiences for a Meta Ads account.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional - will use cached token if not provided)
        limit: Maximum number of audiences to return (default: 25)
        filter_by_subtype: Optional filter by audience subtype. Valid values:
                          CUSTOM, WEBSITE, APP, OFFLINE_CONVERSION, CLAIM,
                          PARTNER, MANAGED, VIDEO, LOOKALIKE, ENGAGEMENT,
                          BAG_OF_ACCOUNTS, STUDY_RULE_AUDIENCE, FOX

    Returns:
        JSON response with custom audiences including id, name, subtype,
        approximate_count, delivery_status, and more.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    endpoint = f"{account_id}/customaudiences"
    params = {
        "fields": "id,name,subtype,description,approximate_count_lower_bound,approximate_count_upper_bound,delivery_status,operation_status,permission_for_actions,data_source,retention_days,rule,lookalike_spec,time_created,time_updated,is_value_based,customer_file_source",
        "limit": limit
    }

    if filter_by_subtype:
        params["filtering"] = json.dumps([{
            "field": "subtype",
            "operator": "EQUAL",
            "value": filter_by_subtype
        }])

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_custom_audience_details(
    audience_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific custom audience.

    Args:
        audience_id: Meta Ads custom audience ID
        access_token: Meta API access token (optional - will use cached token if not provided)

    Returns:
        JSON response with full audience details including targeting rules,
        lookalike spec (if applicable), and delivery status.
    """
    if not audience_id:
        return json.dumps({"error": "No audience ID provided"}, indent=2)

    endpoint = f"{audience_id}"
    params = {
        "fields": "id,name,subtype,description,approximate_count_lower_bound,approximate_count_upper_bound,delivery_status,operation_status,permission_for_actions,data_source,retention_days,rule,rule_aggregation,lookalike_spec,time_created,time_updated,is_value_based,customer_file_source,pixel_id,prefill,inclusions,exclusions,external_event_source"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_saved_audiences(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Get saved audiences (reusable targeting presets) for a Meta Ads account.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional)
        limit: Maximum number of saved audiences to return (default: 25)

    Returns:
        JSON response with saved audiences including targeting specifications.
    """
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)

    endpoint = f"{account_id}/savedaudiences"
    params = {
        "fields": "id,name,description,approximate_count,run_status,targeting,time_created,time_updated,sentence_lines,permission_for_actions",
        "limit": limit
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_saved_audience_details(
    saved_audience_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific saved audience.

    Args:
        saved_audience_id: Meta Ads saved audience ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with full saved audience details including targeting.
    """
    if not saved_audience_id:
        return json.dumps({"error": "No saved audience ID provided"}, indent=2)

    endpoint = f"{saved_audience_id}"
    params = {
        "fields": "id,name,description,approximate_count,run_status,targeting,time_created,time_updated,sentence_lines,permission_for_actions"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)
