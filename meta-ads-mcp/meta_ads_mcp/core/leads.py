"""Lead generation functionality for Meta Ads API.

This module provides read-only tools for viewing lead generation forms and retrieving leads.

IMPORTANT: Lead retrieval requires the 'leads_retrieval' permission.
Add this permission in developers.facebook.com > Your App > App Review > Permissions.

Lead form viewing uses existing 'pages_read_engagement' or 'ads_read' permission.
"""

import json
from typing import Optional, Dict, Any, List
from .api import meta_api_tool, make_api_request
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_lead_forms(
    page_id: str,
    access_token: Optional[str] = None,
    limit: int = 25
) -> str:
    """
    Get lead generation forms for a Facebook Page.

    Args:
        page_id: Facebook Page ID
        access_token: Meta API access token (optional)
        limit: Maximum number of forms to return (default: 25)

    Returns:
        JSON response with lead forms including id, name, status, and questions.

    Permission Required:
        pages_read_engagement or ads_read
    """
    if not page_id:
        return json.dumps({"error": "No page ID provided"}, indent=2)

    endpoint = f"{page_id}/leadgen_forms"
    params = {
        "fields": "id,name,status,leads_count,locale,page,questions,privacy_policy_url,qualifiers,thank_you_page,created_time,expired_leads_count,follow_up_action_url,is_optimized_for_quality,organic_leads_count,page_id",
        "limit": limit
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_lead_form_details(
    form_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific lead form.

    Args:
        form_id: Lead form ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with full form details including all questions and configuration.
    """
    if not form_id:
        return json.dumps({"error": "No form ID provided"}, indent=2)

    endpoint = f"{form_id}"
    params = {
        "fields": "id,name,status,leads_count,locale,page,questions,privacy_policy_url,qualifiers,thank_you_page,created_time,expired_leads_count,follow_up_action_url,is_optimized_for_quality,organic_leads_count,page_id,question_page_custom_headline,tracking_parameters,context_card,legal_content,tcpa_compliance,block_display_for_non_targeted_viewer"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_leads(
    form_id: str,
    access_token: Optional[str] = None,
    limit: int = 50,
    filtering: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Get leads collected by a lead generation form.

    Args:
        form_id: Lead form ID
        access_token: Meta API access token (optional)
        limit: Maximum number of leads to return (default: 50)
        filtering: Optional filters. Example:
                  [{"field": "time_created", "operator": "GREATER_THAN", "value": 1609459200}]

    Returns:
        JSON response with lead data including field values.

    Permission Required:
        leads_retrieval (requires App Review approval)

    Note:
        If you get a permission error, ensure:
        1. Your app has leads_retrieval permission approved
        2. You have a Page access token with leads_retrieval permission
        3. The Page has granted your app access to leads
    """
    if not form_id:
        return json.dumps({"error": "No form ID provided"}, indent=2)

    endpoint = f"{form_id}/leads"
    params = {
        "fields": "id,created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,form_id,is_organic,platform,retailer_item_id",
        "limit": limit
    }

    if filtering:
        params["filtering"] = json.dumps(filtering)

    try:
        data = await make_api_request(endpoint, access_token, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        if "permission" in error_msg.lower() or "leads_retrieval" in error_msg.lower():
            return json.dumps({
                "error": "Permission denied - leads_retrieval permission required",
                "details": error_msg,
                "how_to_fix": {
                    "step_1": "Go to developers.facebook.com",
                    "step_2": "Select your app",
                    "step_3": "Go to App Review > Permissions and Features",
                    "step_4": "Request 'leads_retrieval' permission",
                    "step_5": "Complete the review process with use case description"
                }
            }, indent=2)
        raise


@mcp_server.tool()
@meta_api_tool
async def get_ad_leads(
    ad_id: str,
    access_token: Optional[str] = None,
    limit: int = 50
) -> str:
    """
    Get leads collected by a specific ad.

    Args:
        ad_id: Ad ID
        access_token: Meta API access token (optional)
        limit: Maximum number of leads to return (default: 50)

    Returns:
        JSON response with lead data associated with the ad.

    Permission Required:
        leads_retrieval (requires App Review approval)
    """
    if not ad_id:
        return json.dumps({"error": "No ad ID provided"}, indent=2)

    endpoint = f"{ad_id}/leads"
    params = {
        "fields": "id,created_time,field_data,form_id,is_organic,platform",
        "limit": limit
    }

    try:
        data = await make_api_request(endpoint, access_token, params)
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        if "permission" in error_msg.lower():
            return json.dumps({
                "error": "Permission denied - leads_retrieval permission required",
                "details": error_msg
            }, indent=2)
        raise


@mcp_server.tool()
@meta_api_tool
async def get_page_lead_access(
    page_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Check which apps/users have access to leads for a Page.

    Args:
        page_id: Facebook Page ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with list of apps and users with lead access.
    """
    if not page_id:
        return json.dumps({"error": "No page ID provided"}, indent=2)

    endpoint = f"{page_id}/leadgen_whitelisted_users"
    params = {}

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_lead_gen_quality_score(
    form_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get the quality score for a lead form (if available).

    Args:
        form_id: Lead form ID
        access_token: Meta API access token (optional)

    Returns:
        JSON response with quality metrics for the form.
    """
    if not form_id:
        return json.dumps({"error": "No form ID provided"}, indent=2)

    endpoint = f"{form_id}"
    params = {
        "fields": "id,name,is_optimized_for_quality,leads_count,organic_leads_count,expired_leads_count"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)
