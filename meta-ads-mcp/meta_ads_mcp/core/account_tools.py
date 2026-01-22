"""
MCP tools for multi-tenant account management.

Provides tools for:
- Listing configured accounts
- Switching between accounts
- Checking rate limit status
- Validating credentials
"""

import json
import asyncio
from typing import Optional

from .server import mcp_server
from .credentials import get_credential_manager
from .rate_limiter import get_rate_limiter
from .preflight import run_preflight_checks, format_preflight_result
from .utils import logger


@mcp_server.tool()
async def list_configured_accounts() -> str:
    """
    List all configured Meta Ads accounts.

    Returns account names, display names, ad account IDs, and current status.
    Also includes token expiration alerts if any tokens are expiring soon.

    Returns:
        JSON with list of accounts and their metadata
    """
    credential_manager = get_credential_manager()

    accounts = credential_manager.list_accounts()
    current = credential_manager.get_current_account()

    # Check for token expiration alerts
    alert = credential_manager.check_token_expiration_alerts()

    result = {
        "total_accounts": len(accounts),
        "current_account": current,
        "accounts": accounts
    }

    if alert:
        result["token_expiration_alert"] = alert

    # Add API keys info
    api_keys = credential_manager.list_api_keys()
    result["api_keys"] = api_keys

    return json.dumps(result, indent=2, default=str)


@mcp_server.tool()
async def switch_account(account_name: str) -> str:
    """
    Switch to a different configured account.

    Sets the current active account for subsequent API calls.
    This is session-based and does not persist across restarts.

    Args:
        account_name: Name of the account to switch to (as defined in credentials.json)

    Returns:
        JSON with success status and account details
    """
    credential_manager = get_credential_manager()

    if credential_manager.set_current_account(account_name):
        account = credential_manager.accounts[account_name]
        return json.dumps({
            "success": True,
            "message": f"Switched to {account.display_name}",
            "current_account": account_name,
            "ad_account_id": account.ad_account_id
        }, indent=2)
    else:
        return json.dumps({
            "success": False,
            "error": f"Account '{account_name}' not found",
            "available_accounts": list(credential_manager.accounts.keys())
        }, indent=2)


@mcp_server.tool()
async def get_current_account() -> str:
    """
    Get the currently active account.

    Returns details about the current account including its API key info.

    Returns:
        JSON with current account details
    """
    credential_manager = get_credential_manager()

    current = credential_manager.get_current_account()
    if not current:
        return json.dumps({
            "error": "No account configured",
            "message": "Create credentials.json or set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID environment variables."
        }, indent=2)

    account = credential_manager.accounts[current]
    key = credential_manager.get_key_for_account(current)

    return json.dumps({
        "account_name": current,
        "display_name": account.display_name,
        "ad_account_id": account.ad_account_id,
        "api_key": account.api_key,
        "key_tier": key.tier,
        "key_expires_in_days": key.days_until_expiry
    }, indent=2, default=str)


@mcp_server.tool()
async def get_rate_limit_status() -> str:
    """
    Get current rate limit status for all API keys.

    Shows current usage, blocking status, and call counts for each key.

    Returns:
        JSON with rate limit status per key
    """
    rate_limiter = get_rate_limiter()
    credential_manager = get_credential_manager()

    # Get status for all tracked keys
    status = rate_limiter.get_all_status()

    # Add keys that haven't been used yet
    for key_name in credential_manager.api_keys:
        if key_name not in status:
            status[key_name] = {
                "key_name": key_name,
                "status": "idle",
                "message": "No calls recorded yet",
                "tier": credential_manager.api_keys[key_name].tier
            }

    return json.dumps({
        "rate_limits": status,
        "total_keys": len(credential_manager.api_keys)
    }, indent=2)


@mcp_server.tool()
async def validate_credentials() -> str:
    """
    Run preflight validation on all credentials.

    Validates tokens and account access by making test API calls.
    Run this after updating credentials.json or if you encounter auth errors.

    Returns:
        Formatted validation results showing status of each key and account
    """
    credential_manager = get_credential_manager()

    if not credential_manager.accounts:
        return json.dumps({
            "error": "No accounts configured",
            "message": "Create credentials.json or set environment variables first."
        }, indent=2)

    try:
        result = await run_preflight_checks(credential_manager)
        formatted = format_preflight_result(result)

        # Also return structured data
        return json.dumps({
            "formatted_result": formatted,
            "status": result.status.value,
            "passed": result.passed,
            "key_count": len(result.keys),
            "account_count": len(result.accounts),
            "error_count": len(result.errors),
            "warning_count": len(result.warnings)
        }, indent=2)
    except Exception as e:
        logger.error(f"Preflight validation error: {e}")
        return json.dumps({
            "error": f"Validation failed: {str(e)}",
            "message": "Check that aiohttp is installed and network is available."
        }, indent=2)


@mcp_server.tool()
async def get_token_expiration_status() -> str:
    """
    Check token expiration status for all API keys.

    Returns tokens expiring within 7 days and their affected accounts.

    Returns:
        JSON with expiration warnings and affected accounts
    """
    credential_manager = get_credential_manager()

    expiring = credential_manager.get_expiring_tokens(days_threshold=7)
    alert = credential_manager.check_token_expiration_alerts()

    all_keys = []
    for key in credential_manager.api_keys.values():
        all_keys.append({
            "name": key.name,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "days_until_expiry": key.days_until_expiry,
            "is_expired": key.is_expired
        })

    return json.dumps({
        "expiring_soon": expiring,
        "alert_message": alert,
        "all_keys": all_keys
    }, indent=2, default=str)
