"""Ad Set-related functionality for Meta Ads API."""

import json
from typing import Optional, Dict, Any, List, Union
from .api import meta_api_tool, make_api_request
from .accounts import get_ad_accounts
from .server import mcp_server


@mcp_server.tool()
@meta_api_tool
async def get_adsets(
    account_id: str,
    access_token: Optional[str] = None,
    limit: int = 50,
    campaign_id: str = "",
    time_range: Optional[Union[str, Dict[str, str]]] = None,
    only_with_spend: bool = True
) -> str:
    """
    Get ad sets for a Meta Ads account with optional filtering by campaign.

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional - will use cached token if not provided)
        limit: Maximum number of ad sets to return (default: 50)
        campaign_id: Optional campaign ID to filter by
        time_range: Time range to filter by spend activity. When provided with only_with_spend=True,
                   only returns ad sets that had spend in this period.
                   Presets: today, yesterday, last_7d, last_14d, last_30d, last_90d, this_month, last_month
                   Or custom: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
        only_with_spend: If True and time_range is provided, only returns ad sets with spend > 0
                        in the specified time range. Also includes spend metrics in the response.
                        (default: True)
    """
    # Require explicit account_id
    if not account_id:
        return json.dumps({"error": "No account ID specified"}, indent=2)

    # If only_with_spend is True and time_range provided, filter by spend first
    if only_with_spend and time_range:
        # Fetch insights to get ad sets with spend
        insights_endpoint = f"{account_id}/insights"
        insights_params = {
            "level": "adset",
            "fields": "adset_id,adset_name,campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc,cpm",
            "limit": 500
        }

        # Handle time_range parameter
        if isinstance(time_range, dict):
            insights_params["time_range"] = json.dumps(time_range)
        else:
            insights_params["date_preset"] = time_range

        # Filter by campaign if provided
        if campaign_id:
            insights_params["filtering"] = json.dumps([{
                "field": "campaign.id",
                "operator": "EQUAL",
                "value": campaign_id
            }])

        insights_data = await make_api_request(insights_endpoint, access_token, insights_params)

        if "error" in insights_data:
            return json.dumps(insights_data, indent=2)

        insights_list = insights_data.get("data", [])

        # Filter ad sets with spend > 0
        adsets_with_spend = {}
        for insight in insights_list:
            spend = float(insight.get("spend", 0))
            if spend > 0:
                adset_id = insight.get("adset_id")
                adsets_with_spend[adset_id] = {
                    "spend": insight.get("spend"),
                    "impressions": insight.get("impressions"),
                    "clicks": insight.get("clicks"),
                    "ctr": insight.get("ctr"),
                    "cpc": insight.get("cpc"),
                    "cpm": insight.get("cpm"),
                    "campaign_id": insight.get("campaign_id"),
                    "campaign_name": insight.get("campaign_name"),
                }

        if not adsets_with_spend:
            return json.dumps({
                "data": [],
                "message": "No ad sets with spend found in the specified time range",
                "time_range": time_range,
                "account_id": account_id,
                "campaign_id": campaign_id if campaign_id else None
            }, indent=2)

        # Fetch ad set details for ad sets with spend
        adset_ids = list(adsets_with_spend.keys())

        # Apply limit
        if len(adset_ids) > limit:
            adset_ids = adset_ids[:limit]

        # Fetch each ad set's details and merge with spend data
        result_adsets = []
        for adset_id in adset_ids:
            adset_endpoint = f"{adset_id}"
            adset_params = {
                "fields": "id,name,campaign_id,status,daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,is_dynamic_creative"
            }

            adset_data = await make_api_request(adset_endpoint, access_token, adset_params)

            if "error" not in adset_data:
                # Merge spend data
                adset_data["performance"] = adsets_with_spend[adset_id]
                result_adsets.append(adset_data)

        return json.dumps({
            "data": result_adsets,
            "summary": {
                "total_adsets_with_spend": len(result_adsets),
                "time_range": time_range,
                "total_spend": sum(float(a["performance"]["spend"]) for a in result_adsets),
                "campaign_id": campaign_id if campaign_id else None,
                "message": f"Showing {len(result_adsets)} ad sets with ad spend in the selected period. Set only_with_spend=False to include all ad sets."
            }
        }, indent=2)

    # Standard flow: fetch all ad sets without spend filtering
    # Change endpoint based on whether campaign_id is provided
    if campaign_id:
        endpoint = f"{campaign_id}/adsets"
        params = {
            "fields": "id,name,campaign_id,status,daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,is_dynamic_creative,frequency_control_specs{event,interval_days,max_frequency}",
            "limit": limit
        }
    else:
        # Use account endpoint if no campaign_id is given
        endpoint = f"{account_id}/adsets"
        params = {
            "fields": "id,name,campaign_id,status,daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,is_dynamic_creative,frequency_control_specs{event,interval_days,max_frequency}",
            "limit": limit
        }

    data = await make_api_request(endpoint, access_token, params)

    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_adset_details(adset_id: str, access_token: Optional[str] = None) -> str:
    """
    Get detailed information about a specific ad set.
    
    Args:
        adset_id: Meta Ads ad set ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Example:
        To call this function through MCP, pass the adset_id as the first argument:
        {
            "args": "YOUR_ADSET_ID"
        }
    """
    if not adset_id:
        return json.dumps({"error": "No ad set ID provided"}, indent=2)
    
    endpoint = f"{adset_id}"
    # Explicitly prioritize frequency_control_specs in the fields request
    params = {
        "fields": "id,name,campaign_id,status,frequency_control_specs{event,interval_days,max_frequency},daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,attribution_spec,destination_type,promoted_object,pacing_type,budget_remaining,dsa_beneficiary,is_dynamic_creative"
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    # For debugging - check if frequency_control_specs was returned
    if 'frequency_control_specs' not in data:
        data['_meta'] = {
            'note': 'No frequency_control_specs field was returned by the API. This means either no frequency caps are set or the API did not include this field in the response.'
        }
    
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def create_adset(
    account_id: str, 
    campaign_id: str, 
    name: str,
    optimization_goal: str,
    billing_event: str,
    status: str = "PAUSED",
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    targeting: Optional[Dict[str, Any]] = None,
    bid_amount: Optional[int] = None,
    bid_strategy: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    dsa_beneficiary: Optional[str] = None,
    promoted_object: Optional[Dict[str, Any]] = None,
    destination_type: Optional[str] = None,
    is_dynamic_creative: Optional[bool] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Create a new ad set in a Meta Ads account.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        campaign_id: Meta Ads campaign ID this ad set belongs to
        name: Ad set name
        optimization_goal: Conversion optimization goal (e.g., 'LINK_CLICKS', 'REACH', 'CONVERSIONS', 'APP_INSTALLS')
        billing_event: How you're charged (e.g., 'IMPRESSIONS', 'LINK_CLICKS')
        status: Initial ad set status (default: PAUSED)
        daily_budget: Daily budget in account currency (in cents) as a string
        lifetime_budget: Lifetime budget in account currency (in cents) as a string
        targeting: Targeting specifications including age, location, interests, etc.
                  Use targeting_automation.advantage_audience=1 for automatic audience finding
        bid_amount: Bid amount in account currency (in cents)
        bid_strategy: Bid strategy (e.g., 'LOWEST_COST', 'LOWEST_COST_WITH_BID_CAP')
        start_time: Start time in ISO 8601 format (e.g., '2023-12-01T12:00:00-0800')
        end_time: End time in ISO 8601 format
        dsa_beneficiary: DSA beneficiary (person/organization benefiting from ads) for European compliance
        promoted_object: Mobile app configuration for APP_INSTALLS campaigns. Required fields: application_id, object_store_url.
                        Optional fields: custom_event_type, pixel_id, page_id.
                        Example: {"application_id": "123456789012345", "object_store_url": "https://apps.apple.com/app/id123456789"}
        destination_type: Where users are directed after clicking the ad (e.g., 'APP_STORE', 'DEEPLINK', 'APP_INSTALL', 'ON_AD').
                          Required for mobile app campaigns and lead generation campaigns.
                          Use 'ON_AD' for lead generation campaigns where user interaction happens within the ad.
        is_dynamic_creative: Enable Dynamic Creative for this ad set (required when using dynamic creatives with asset_feed_spec/dynamic_creative_spec).
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    # Check required parameters
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)
    
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)
    
    if not name:
        return json.dumps({"error": "No ad set name provided"}, indent=2)
    
    if not optimization_goal:
        return json.dumps({"error": "No optimization goal provided"}, indent=2)
    
    if not billing_event:
        return json.dumps({"error": "No billing event provided"}, indent=2)
    
    # Validate mobile app parameters for APP_INSTALLS campaigns
    if optimization_goal == "APP_INSTALLS":
        if not promoted_object:
            return json.dumps({
                "error": "promoted_object is required for APP_INSTALLS optimization goal",
                "details": "Mobile app campaigns must specify which app is being promoted",
                "required_fields": ["application_id", "object_store_url"]
            }, indent=2)
        
        # Validate promoted_object structure
        if not isinstance(promoted_object, dict):
            return json.dumps({
                "error": "promoted_object must be a dictionary",
                "example": {"application_id": "123456789012345", "object_store_url": "https://apps.apple.com/app/id123456789"}
            }, indent=2)
        
        # Validate required promoted_object fields
        if "application_id" not in promoted_object:
            return json.dumps({
                "error": "promoted_object missing required field: application_id",
                "details": "application_id is the Facebook app ID for your mobile app"
            }, indent=2)
        
        if "object_store_url" not in promoted_object:
            return json.dumps({
                "error": "promoted_object missing required field: object_store_url", 
                "details": "object_store_url should be the App Store or Google Play URL for your app"
            }, indent=2)
        
        # Validate store URL format
        store_url = promoted_object["object_store_url"]
        valid_store_patterns = [
            "apps.apple.com",  # iOS App Store
            "play.google.com",  # Google Play Store
            "itunes.apple.com"  # Alternative iOS format
        ]
        
        if not any(pattern in store_url for pattern in valid_store_patterns):
            return json.dumps({
                "error": "Invalid object_store_url format",
                "details": "URL must be from App Store (apps.apple.com) or Google Play (play.google.com)",
                "provided_url": store_url
            }, indent=2)
    
    # Validate destination_type if provided
    if destination_type:
        valid_destination_types = ["APP_STORE", "DEEPLINK", "APP_INSTALL", "ON_AD"]
        if destination_type not in valid_destination_types:
            return json.dumps({
                "error": f"Invalid destination_type: {destination_type}",
                "valid_values": valid_destination_types
            }, indent=2)
    
    # Basic targeting is required if not provided
    if not targeting:
        targeting = {
            "age_min": 18,
            "age_max": 65,
            "geo_locations": {"countries": ["US"]},
            "targeting_automation": {"advantage_audience": 1}
        }
    
    endpoint = f"{account_id}/adsets"
    
    params = {
        "name": name,
        "campaign_id": campaign_id,
        "status": status,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
        "targeting": json.dumps(targeting)  # Properly format as JSON string
    }
    
    # Convert budget values to strings if they aren't already
    if daily_budget is not None:
        params["daily_budget"] = str(daily_budget)
    
    if lifetime_budget is not None:
        params["lifetime_budget"] = str(lifetime_budget)
    
    # Add other parameters if provided
    if bid_amount is not None:
        params["bid_amount"] = str(bid_amount)
    
    if bid_strategy:
        params["bid_strategy"] = bid_strategy
    
    if start_time:
        params["start_time"] = start_time
    
    if end_time:
        params["end_time"] = end_time
    
    # Add DSA beneficiary if provided
    if dsa_beneficiary:
        params["dsa_beneficiary"] = dsa_beneficiary
    
    # Add mobile app parameters if provided
    if promoted_object:
        params["promoted_object"] = json.dumps(promoted_object)
    
    if destination_type:
        params["destination_type"] = destination_type
    
    # Enable Dynamic Creative if requested
    if is_dynamic_creative is not None:
        params["is_dynamic_creative"] = "true" if bool(is_dynamic_creative) else "false"
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        
        # Enhanced error handling for DSA beneficiary issues
        if "permission" in error_msg.lower() or "insufficient" in error_msg.lower():
            return json.dumps({
                "error": "Insufficient permissions to set DSA beneficiary. Please ensure you have business_management permissions.",
                "details": error_msg,
                "params_sent": params,
                "permission_required": True
            }, indent=2)
        elif "dsa_beneficiary" in error_msg.lower() and ("not supported" in error_msg.lower() or "parameter" in error_msg.lower()):
            return json.dumps({
                "error": "DSA beneficiary parameter not supported in this API version. Please set DSA beneficiary manually in Facebook Ads Manager.",
                "details": error_msg,
                "params_sent": params,
                "manual_setup_required": True
            }, indent=2)
        elif "benefits from ads" in error_msg or "DSA beneficiary" in error_msg:
            return json.dumps({
                "error": "DSA beneficiary required for European compliance. Please provide the person or organization that benefits from ads in this ad set.",
                "details": error_msg,
                "params_sent": params,
                "dsa_required": True
            }, indent=2)
        else:
            return json.dumps({
                "error": "Failed to create ad set",
                "details": error_msg,
                "params_sent": params
            }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def update_adset(adset_id: str, frequency_control_specs: Optional[List[Dict[str, Any]]] = None, bid_strategy: Optional[str] = None, 
                        bid_amount: Optional[int] = None, status: Optional[str] = None, targeting: Optional[Dict[str, Any]] = None, 
                        optimization_goal: Optional[str] = None, daily_budget: Optional[int] = None, lifetime_budget: Optional[int] = None, 
                        is_dynamic_creative: Optional[bool] = None,
                        access_token: Optional[str] = None) -> str:
    """
    Update an ad set with new settings including frequency caps and budgets.
    
    Args:
        adset_id: Meta Ads ad set ID
        frequency_control_specs: List of frequency control specifications 
                                 (e.g. [{"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}])
        bid_strategy: Bid strategy (e.g., 'LOWEST_COST_WITH_BID_CAP')
        bid_amount: Bid amount in account currency (in cents for USD)
        status: Update ad set status (ACTIVE, PAUSED, etc.)
        targeting: Complete targeting specifications (will replace existing targeting)
                  (e.g. {"targeting_automation":{"advantage_audience":1}, "geo_locations": {"countries": ["US"]}})
        optimization_goal: Conversion optimization goal (e.g., 'LINK_CLICKS', 'CONVERSIONS', 'APP_INSTALLS', etc.)
        daily_budget: Daily budget in account currency (in cents) as a string
        lifetime_budget: Lifetime budget in account currency (in cents) as a string
        is_dynamic_creative: Enable/disable Dynamic Creative for this ad set.
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not adset_id:
        return json.dumps({"error": "No ad set ID provided"}, indent=2)
    
    params = {}
    
    if frequency_control_specs is not None:
        # api.py will handle JSON encoding for lists/dicts in POST requests
        params['frequency_control_specs'] = frequency_control_specs
    
    if bid_strategy is not None:
        params['bid_strategy'] = bid_strategy
        
    if bid_amount is not None:
        params['bid_amount'] = str(bid_amount)
        
    if status is not None:
        params['status'] = status
        
    if optimization_goal is not None:
        params['optimization_goal'] = optimization_goal
        
    if targeting is not None:
        # Ensure proper JSON encoding for targeting
        if isinstance(targeting, dict):
            params['targeting'] = json.dumps(targeting)
        else:
            params['targeting'] = targeting  # Already a string
    
    # Add budget parameters if provided
    if daily_budget is not None:
        params['daily_budget'] = str(daily_budget)
    
    if lifetime_budget is not None:
        params['lifetime_budget'] = str(lifetime_budget)
    
    if is_dynamic_creative is not None:
        params['is_dynamic_creative'] = "true" if bool(is_dynamic_creative) else "false"
    
    if not params:
        return json.dumps({"error": "No update parameters provided"}, indent=2)

    endpoint = f"{adset_id}"
    
    try:
        # Use POST method for updates as per Meta API documentation
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        # Include adset_id in error for better context
        return json.dumps({
            "error": f"Failed to update ad set {adset_id}",
            "details": error_msg,
            "params_sent": params
        }, indent=2) 