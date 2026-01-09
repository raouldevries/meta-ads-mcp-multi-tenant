"""Account-related functionality for Meta Ads API."""

import json
import time
import httpx
from typing import Optional, Dict, Any
from .api import meta_api_tool, make_api_request, META_GRAPH_API_BASE
from .server import mcp_server
from .auth import get_current_access_token


@mcp_server.tool()
@meta_api_tool
async def get_ad_accounts(access_token: Optional[str] = None, user_id: str = "me", limit: int = 200) -> str:
    """
    Get ad accounts accessible by a user.
    
    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        user_id: Meta user ID or "me" for the current user
        limit: Maximum number of accounts to return (default: 200)
    """
    endpoint = f"{user_id}/adaccounts"
    params = {
        "fields": "id,name,account_id,account_status,amount_spent,balance,currency,age,business_city,business_country_code",
        "limit": limit
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@mcp_server.tool()
@meta_api_tool
async def get_account_info(account_id: str, access_token: Optional[str] = None) -> str:
    """
    Get detailed information about a specific ad account.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return {
            "error": {
                "message": "Account ID is required",
                "details": "Please specify an account_id parameter",
                "example": "Use account_id='act_123456789' or account_id='123456789'"
            }
        }
    
    # Ensure account_id has the 'act_' prefix for API compatibility
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    
    # Try to get the account info directly first
    endpoint = f"{account_id}"
    params = {
        "fields": "id,name,account_id,account_status,amount_spent,balance,currency,age,business_city,business_country_code,timezone_name"
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    # Check if the API request returned an error
    if "error" in data:
        # If access was denied, provide helpful error message with accessible accounts
        if "access" in str(data.get("error", {})).lower() or "permission" in str(data.get("error", {})).lower():
            # Get list of accessible accounts for helpful error message
            accessible_endpoint = "me/adaccounts"
            accessible_params = {
                "fields": "id,name,account_id,account_status,amount_spent,balance,currency,age,business_city,business_country_code",
                "limit": 50
            }
            accessible_accounts_data = await make_api_request(accessible_endpoint, access_token, accessible_params)
            
            if "data" in accessible_accounts_data:
                accessible_accounts = [
                    {"id": acc["id"], "name": acc["name"]} 
                    for acc in accessible_accounts_data["data"][:10]  # Show first 10
                ]
                return {
                    "error": {
                        "message": f"Account {account_id} is not accessible to your user account",
                        "details": "This account either doesn't exist or you don't have permission to access it",
                        "accessible_accounts": accessible_accounts,
                        "total_accessible_accounts": len(accessible_accounts_data["data"]),
                        "suggestion": "Try using one of the accessible account IDs listed above"
                    }
                }
        
        # Return the original error for non-permission related issues
        return data
    
    # Add DSA requirement detection
    if "business_country_code" in data:
        european_countries = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE", "DK", "SE", "FI", "NO"]
        if data["business_country_code"] in european_countries:
            data["dsa_required"] = True
            data["dsa_compliance_note"] = "This account is subject to European DSA (Digital Services Act) requirements"
        else:
            data["dsa_required"] = False
            data["dsa_compliance_note"] = "This account is not subject to European DSA requirements"
    
    return data


@mcp_server.tool()
async def health_check(access_token: Optional[str] = None) -> str:
    """
    Validate Meta API connectivity and token status.

    Performs:
    1. Token validation (checks if token is valid)
    2. Permission check (lists accessible ad accounts)
    3. API latency measurement

    Returns:
        JSON with health status, token info, and diagnostics
    """
    start_time = time.time()
    result = {
        "status": "unknown",
        "checks": {},
        "diagnostics": {}
    }

    try:
        # Get token
        token = access_token or await get_current_access_token()
        if not token:
            result["status"] = "error"
            result["checks"]["token"] = {
                "status": "failed",
                "message": "No access token configured"
            }
            return json.dumps(result, indent=2)

        result["checks"]["token"] = {
            "status": "present",
            "prefix": token[:20] + "..." if len(token) > 20 else token
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test API connectivity with debug_token call
            token_check_start = time.time()
            try:
                debug_url = f"{META_GRAPH_API_BASE}/debug_token"
                params = {
                    "input_token": token,
                    "access_token": token
                }

                response = await client.get(debug_url, params=params)
                token_data = response.json()
                token_check_time = time.time() - token_check_start

                if "data" in token_data:
                    data = token_data["data"]
                    result["checks"]["token_validation"] = {
                        "status": "valid" if data.get("is_valid") else "invalid",
                        "app_id": data.get("app_id"),
                        "type": data.get("type"),
                        "expires_at": data.get("expires_at", 0),
                        "scopes": data.get("scopes", []),
                        "latency_ms": round(token_check_time * 1000)
                    }
                else:
                    error_msg = token_data.get("error", {})
                    result["checks"]["token_validation"] = {
                        "status": "error",
                        "error": error_msg.get("message", "Unknown error") if isinstance(error_msg, dict) else str(error_msg)
                    }

            except Exception as e:
                result["checks"]["token_validation"] = {
                    "status": "error",
                    "error": str(e)
                }

            # Test ad accounts access
            accounts_start = time.time()
            try:
                accounts_url = f"{META_GRAPH_API_BASE}/me/adaccounts"
                params = {
                    "access_token": token,
                    "fields": "id,name,account_status",
                    "limit": 5
                }

                response = await client.get(accounts_url, params=params)
                accounts_data = response.json()
                accounts_time = time.time() - accounts_start

                if "data" in accounts_data:
                    result["checks"]["ad_accounts"] = {
                        "status": "accessible",
                        "count": len(accounts_data["data"]),
                        "sample": [
                            {"id": acc["id"], "name": acc.get("name", "N/A")}
                            for acc in accounts_data["data"][:3]
                        ],
                        "latency_ms": round(accounts_time * 1000)
                    }
                else:
                    error_msg = accounts_data.get("error", {})
                    result["checks"]["ad_accounts"] = {
                        "status": "error",
                        "error": error_msg.get("message", "Unknown error") if isinstance(error_msg, dict) else str(error_msg)
                    }

            except Exception as e:
                result["checks"]["ad_accounts"] = {
                    "status": "error",
                    "error": str(e)
                }

        # Determine overall status
        token_ok = result["checks"].get("token_validation", {}).get("status") == "valid"
        accounts_ok = result["checks"].get("ad_accounts", {}).get("status") == "accessible"

        if token_ok and accounts_ok:
            result["status"] = "healthy"
        elif token_ok:
            result["status"] = "degraded"
        else:
            result["status"] = "unhealthy"

        # Add diagnostics
        total_time = time.time() - start_time
        result["diagnostics"] = {
            "total_latency_ms": round(total_time * 1000),
            "api_base": META_GRAPH_API_BASE,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return json.dumps(result, indent=2)