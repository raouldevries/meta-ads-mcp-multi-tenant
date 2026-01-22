"""Campaign-related functionality for Meta Ads API."""

import json
from typing import List, Optional, Dict, Any, Union
from .api import meta_api_tool, make_api_request
from .pagination import fetch_all_pages
from .credentials import get_credential_manager

# Type alias for budget values that can be int (cents) or empty string (to remove)
BudgetValue = Union[int, str, None]
from .accounts import get_ad_accounts
from .server import mcp_server


def _resolve_account_id(account_id: Optional[str], account_name: Optional[str]) -> Optional[str]:
    """
    Resolve account_id from account_name if provided.

    Args:
        account_id: Explicit account ID (takes precedence)
        account_name: Named account from credentials.json

    Returns:
        Resolved account ID, or None if not found
    """
    if account_id:
        return account_id

    if account_name:
        try:
            credential_manager = get_credential_manager()
            return credential_manager.get_account_id(account_name)
        except Exception:
            pass

    # Try to get from current account
    try:
        credential_manager = get_credential_manager()
        return credential_manager.get_account_id()
    except Exception:
        pass

    return None


@mcp_server.tool()
@meta_api_tool
async def get_campaigns(
    account_id: Optional[str] = None,
    account_name: Optional[str] = None,
    access_token: Optional[str] = None,
    limit: int = 50,
    status_filter: str = "",
    objective_filter: Union[str, List[str]] = "",
    after: str = "",
    fetch_all: bool = False,
    max_pages: int = 100,
    time_range: Optional[Union[str, Dict[str, str]]] = None,
    only_with_spend: bool = True
) -> str:
    """
    Get campaigns for a Meta Ads account with optional filtering.

    Note: By default, the Meta API returns a subset of available fields.
    Other fields like 'effective_status', 'special_ad_categories',
    'lifetime_budget', 'spend_cap', 'budget_remaining', 'promoted_object',
    'source_campaign_id', etc., might be available but require specifying them
    in the API call (currently not exposed by this tool's parameters).

    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX). Optional if account_name is provided.
        account_name: Named account from credentials.json. If provided, account_id is derived from it.
        access_token: Meta API access token (optional - will use cached token if not provided)
        limit: Maximum number of campaigns to return (default: 50)
        status_filter: Filter by effective status (e.g., 'ACTIVE', 'PAUSED', 'ARCHIVED').
                       Maps to the 'effective_status' API parameter, which expects an array
                       (this function handles the required JSON formatting). Leave empty for all statuses.
        objective_filter: Filter by campaign objective(s). Can be a single objective string or a list of objectives.
                         Valid objectives: 'OUTCOME_AWARENESS', 'OUTCOME_TRAFFIC', 'OUTCOME_ENGAGEMENT',
                         'OUTCOME_LEADS', 'OUTCOME_SALES', 'OUTCOME_APP_PROMOTION'.
                         Examples: 'OUTCOME_LEADS' or ['OUTCOME_LEADS', 'OUTCOME_SALES'].
                         Leave empty for all objectives.
        after: Pagination cursor to get the next set of results
        fetch_all: If True, automatically fetches all pages (default: False)
        max_pages: Maximum pages to fetch when fetch_all=True (default: 100)
        time_range: Time range to filter by spend activity. When provided with only_with_spend=True,
                   only returns campaigns that had spend in this period.
                   Presets: today, yesterday, last_7d, last_14d, last_30d, last_90d, this_month, last_month
                   Or custom: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
        only_with_spend: If True and time_range is provided, only returns campaigns with spend > 0
                        in the specified time range. Also includes spend metrics in the response.
                        (default: True)
    """
    # Resolve account_id from account_name if needed
    account_id = _resolve_account_id(account_id, account_name)

    # Require account_id
    if not account_id:
        return json.dumps({"error": "No account ID specified"}, indent=2)

    # If only_with_spend is True and time_range provided, filter by spend first
    if only_with_spend and time_range:
        # Fetch insights to get campaigns with spend
        insights_endpoint = f"{account_id}/insights"
        insights_params = {
            "level": "campaign",
            "fields": "campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc,cpm",
            "limit": 500
        }

        # Handle time_range parameter
        if isinstance(time_range, dict):
            insights_params["time_range"] = json.dumps(time_range)
        else:
            insights_params["date_preset"] = time_range

        insights_data = await make_api_request(insights_endpoint, access_token, insights_params)

        if "error" in insights_data:
            return json.dumps(insights_data, indent=2)

        insights_list = insights_data.get("data", [])

        # Filter campaigns with spend > 0
        campaigns_with_spend = {}
        for insight in insights_list:
            spend = float(insight.get("spend", 0))
            if spend > 0:
                campaign_id = insight.get("campaign_id")
                campaigns_with_spend[campaign_id] = {
                    "spend": insight.get("spend"),
                    "impressions": insight.get("impressions"),
                    "clicks": insight.get("clicks"),
                    "ctr": insight.get("ctr"),
                    "cpc": insight.get("cpc"),
                    "cpm": insight.get("cpm"),
                }

        if not campaigns_with_spend:
            return json.dumps({
                "data": [],
                "message": "No campaigns with spend found in the specified time range",
                "time_range": time_range,
                "account_id": account_id
            }, indent=2)

        # Fetch campaign details for campaigns with spend
        campaign_ids = list(campaigns_with_spend.keys())

        # Apply limit
        if len(campaign_ids) > limit:
            campaign_ids = campaign_ids[:limit]

        # Fetch each campaign's details and merge with spend data
        result_campaigns = []
        for campaign_id in campaign_ids:
            campaign_endpoint = f"{campaign_id}"
            campaign_params = {
                "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy"
            }

            # Apply status and objective filters if provided
            campaign_data = await make_api_request(campaign_endpoint, access_token, campaign_params)

            if "error" not in campaign_data:
                # Check status filter
                if status_filter and campaign_data.get("status") != status_filter:
                    continue

                # Check objective filter
                if objective_filter:
                    objectives = [objective_filter] if isinstance(objective_filter, str) else objective_filter
                    if campaign_data.get("objective") not in objectives:
                        continue

                # Merge spend data
                campaign_data["performance"] = campaigns_with_spend[campaign_id]
                result_campaigns.append(campaign_data)

        return json.dumps({
            "data": result_campaigns,
            "summary": {
                "total_campaigns_with_spend": len(result_campaigns),
                "time_range": time_range,
                "total_spend": sum(float(c["performance"]["spend"]) for c in result_campaigns),
                "message": f"Showing {len(result_campaigns)} campaigns with ad spend in the selected period. Set only_with_spend=False to include all campaigns."
            }
        }, indent=2)

    # Standard flow: fetch all campaigns without spend filtering
    endpoint = f"{account_id}/campaigns"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy",
        "limit": limit
    }

    # Build filtering array for complex filtering
    filters = []

    if status_filter:
        # API expects an array, encode it as a JSON string
        params["effective_status"] = json.dumps([status_filter])

    # Handle objective filtering - supports both single string and list of objectives
    if objective_filter:
        # Convert single string to list for consistent handling
        objectives = [objective_filter] if isinstance(objective_filter, str) else objective_filter

        # Filter out empty strings
        objectives = [obj for obj in objectives if obj]

        if objectives:
            filters.append({
                "field": "objective",
                "operator": "IN",
                "value": objectives
            })

    # Add filtering parameter if we have filters
    if filters:
        params["filtering"] = json.dumps(filters)

    # Use pagination helper for fetch_all mode
    if fetch_all:
        from .auth import get_current_access_token
        token = access_token or await get_current_access_token()
        if not token:
            return json.dumps({"error": "No access token available"}, indent=2)

        result = await fetch_all_pages(
            endpoint=endpoint,
            params=params,
            access_token=token,
            max_pages=max_pages
        )
        return json.dumps(result, indent=2)

    # Standard single-page request
    if after:
        params["after"] = after

    data = await make_api_request(endpoint, access_token, params)

    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_campaign_details(campaign_id: str, access_token: Optional[str] = None) -> str:
    """
    Get detailed information about a specific campaign.

    Note: This function requests a specific set of fields ('id,name,objective,status,...'). 
    The Meta API offers many other fields for campaigns (e.g., 'effective_status', 'source_campaign_id', etc.) 
    that could be added to the 'fields' parameter in the code if needed.
    
    Args:
        campaign_id: Meta Ads campaign ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)
    
    endpoint = f"{campaign_id}"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy,special_ad_categories,special_ad_category_country,budget_remaining,configured_status"
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def create_campaign(
    account_id: str,
    name: str,
    objective: str,
    access_token: Optional[str] = None,
    status: str = "PAUSED",
    special_ad_categories: Optional[List[str]] = None,
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    buying_type: Optional[str] = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[int] = None,
    spend_cap: Optional[int] = None,
    campaign_budget_optimization: Optional[bool] = None,
    ab_test_control_setups: Optional[List[Dict[str, Any]]] = None,
    use_adset_level_budgets: bool = False
) -> str:
    """
    Create a new campaign in a Meta Ads account.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        name: Campaign name
        objective: Campaign objective (ODAX, outcome-based). Must be one of:
                   OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT,
                   OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_APP_PROMOTION.
                   Note: Legacy objectives like BRAND_AWARENESS, LINK_CLICKS,
                   CONVERSIONS, APP_INSTALLS, etc. are not valid for new
                   campaigns and will cause a 400 error. Use the outcome-based
                   values above (e.g., BRAND_AWARENESS → OUTCOME_AWARENESS).
        access_token: Meta API access token (optional - will use cached token if not provided)
        status: Initial campaign status (default: PAUSED)
        special_ad_categories: List of special ad categories if applicable
        daily_budget: Daily budget in account currency (in cents) as a string (only used if use_adset_level_budgets=False)
        lifetime_budget: Lifetime budget in account currency (in cents) as a string (only used if use_adset_level_budgets=False)
        buying_type: Buying type (e.g., 'AUCTION')
        bid_strategy: Bid strategy. Must be one of: 'LOWEST_COST_WITHOUT_CAP', 'LOWEST_COST_WITH_BID_CAP', 'COST_CAP', 'LOWEST_COST_WITH_MIN_ROAS'.
        bid_cap: Bid cap in account currency (in cents) as a string
        spend_cap: Spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Whether to enable campaign budget optimization (only used if use_adset_level_budgets=False)
        ab_test_control_setups: Settings for A/B testing (e.g., [{"name":"Creative A", "ad_format":"SINGLE_IMAGE"}])
        use_adset_level_budgets: If True, budgets will be set at the ad set level instead of campaign level (default: False)
    """
    # Check required parameters
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)
    
    if not name:
        return json.dumps({"error": "No campaign name provided"}, indent=2)
        
    if not objective:
        return json.dumps({"error": "No campaign objective provided"}, indent=2)
    
    # Special_ad_categories is required by the API, set default if not provided
    if special_ad_categories is None:
        special_ad_categories = []
    
    # For this example, we'll add a fixed daily budget if none is provided and we're not using ad set level budgets
    if not daily_budget and not lifetime_budget and not use_adset_level_budgets:
        daily_budget = 1000  # Default to $10 USD (in cents)
    
    endpoint = f"{account_id}/campaigns"
    
    params = {
        "name": name,
        "objective": objective,
        "status": status,
        "special_ad_categories": json.dumps(special_ad_categories)  # Properly format as JSON string
    }
    
    # Only set campaign-level budgets if we're not using ad set level budgets
    if not use_adset_level_budgets:
        # Convert budget values to strings if they aren't already
        if daily_budget is not None:
            params["daily_budget"] = str(daily_budget)
        
        if lifetime_budget is not None:
            params["lifetime_budget"] = str(lifetime_budget)
        
        if campaign_budget_optimization is not None:
            params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    
    # Add new parameters
    if buying_type:
        params["buying_type"] = buying_type
    
    if bid_strategy:
        params["bid_strategy"] = bid_strategy
    
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    
    if ab_test_control_setups:
        params["ab_test_control_setups"] = json.dumps(ab_test_control_setups)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        
        # Add a note about budget strategy if using ad set level budgets
        if use_adset_level_budgets:
            data["budget_strategy"] = "ad_set_level"
            data["note"] = "Campaign created with ad set level budgets. Set budgets when creating ad sets within this campaign."
        
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return json.dumps({
            "error": "Failed to create campaign",
            "details": error_msg,
            "params_sent": params
        }, indent=2)


@mcp_server.tool()
@meta_api_tool
async def update_campaign(
    campaign_id: str,
    access_token: Optional[str] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    special_ad_categories: Optional[List[str]] = None,
    daily_budget: BudgetValue = None,
    lifetime_budget: BudgetValue = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[int] = None,
    spend_cap: Optional[int] = None,
    campaign_budget_optimization: Optional[bool] = None,
    objective: Optional[str] = None,  # Add objective if it's updatable
    use_adset_level_budgets: Optional[bool] = None,  # Add other updatable fields as needed based on API docs
) -> str:
    """
    Update an existing campaign in a Meta Ads account.

    Args:
        campaign_id: Meta Ads campaign ID
        access_token: Meta API access token (optional - will use cached token if not provided)
        name: New campaign name
        status: New campaign status (e.g., 'ACTIVE', 'PAUSED')
        special_ad_categories: List of special ad categories if applicable
        daily_budget: New daily budget in account currency (in cents) as a string. 
                     Set to empty string "" to remove the daily budget.
        lifetime_budget: New lifetime budget in account currency (in cents) as a string.
                        Set to empty string "" to remove the lifetime budget.
        bid_strategy: New bid strategy
        bid_cap: New bid cap in account currency (in cents) as a string
        spend_cap: New spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Enable/disable campaign budget optimization
        objective: New campaign objective (Note: May not always be updatable)
        use_adset_level_budgets: If True, removes campaign-level budgets to switch to ad set level budgets
    """
    if not campaign_id:
        return json.dumps({"error": "No campaign ID provided"}, indent=2)

    endpoint = f"{campaign_id}"
    
    params = {}
    
    # Add parameters to the request only if they are provided
    if name is not None:
        params["name"] = name
    if status is not None:
        params["status"] = status
    if special_ad_categories is not None:
        # Note: Updating special_ad_categories might have specific API rules or might not be allowed after creation.
        # The API might require an empty list `[]` to clear categories. Check Meta Docs.
        params["special_ad_categories"] = json.dumps(special_ad_categories)
    
    # Handle budget parameters based on use_adset_level_budgets setting
    if use_adset_level_budgets is not None:
        if use_adset_level_budgets:
            # Remove campaign-level budgets when switching to ad set level budgets
            params["daily_budget"] = ""
            params["lifetime_budget"] = ""
            if campaign_budget_optimization is not None:
                params["campaign_budget_optimization"] = "false"
        else:
            # If switching back to campaign-level budgets, use the provided budget values
            if daily_budget is not None:
                if daily_budget == "":
                    params["daily_budget"] = ""
                else:
                    params["daily_budget"] = str(daily_budget)
            if lifetime_budget is not None:
                if lifetime_budget == "":
                    params["lifetime_budget"] = ""
                else:
                    params["lifetime_budget"] = str(lifetime_budget)
            if campaign_budget_optimization is not None:
                params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    else:
        # Normal budget updates when not changing budget strategy
        if daily_budget is not None:
            # To remove budget, set to empty string
            if daily_budget == "":
                params["daily_budget"] = ""
            else:
                params["daily_budget"] = str(daily_budget)
        if lifetime_budget is not None:
            # To remove budget, set to empty string
            if lifetime_budget == "":
                params["lifetime_budget"] = ""
            else:
                params["lifetime_budget"] = str(lifetime_budget)
        if campaign_budget_optimization is not None:
            params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    
    if bid_strategy is not None:
        params["bid_strategy"] = bid_strategy
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    if objective is not None:
        params["objective"] = objective # Caution: Objective changes might reset learning or be restricted

    if not params:
        return json.dumps({"error": "No update parameters provided"}, indent=2)

    try:
        # Use POST method for updates as per Meta API documentation
        data = await make_api_request(endpoint, access_token, params, method="POST")
        
        # Add a note about budget strategy if switching to ad set level budgets
        if use_adset_level_budgets is not None and use_adset_level_budgets:
            data["budget_strategy"] = "ad_set_level"
            data["note"] = "Campaign updated to use ad set level budgets. Set budgets when creating ad sets within this campaign."
        
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        # Include campaign_id in error for better context
        return json.dumps({
            "error": f"Failed to update campaign {campaign_id}",
            "details": error_msg,
            "params_sent": params # Be careful about logging sensitive data if any
        }, indent=2) 