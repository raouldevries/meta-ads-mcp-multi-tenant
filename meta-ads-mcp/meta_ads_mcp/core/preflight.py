"""
Startup preflight checks for credentials validation.

Validates:
- Token validity (can call /me)
- Account accessibility (can call /act_{id})
- Permission verification (has ads_read)
"""

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional
from enum import Enum
import logging

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

if TYPE_CHECKING:
    from .credentials import CredentialManager

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class PreflightStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class KeyValidationResult:
    """Result of validating a single API key."""
    key_name: str
    status: PreflightStatus
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AccountValidationResult:
    """Result of validating a single account."""
    account_name: str
    status: PreflightStatus
    account_id: Optional[str] = None
    account_status: Optional[str] = None
    business_name: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PreflightResult:
    """Overall preflight validation result."""
    status: PreflightStatus
    keys: List[KeyValidationResult] = field(default_factory=list)
    accounts: List[AccountValidationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == PreflightStatus.PASSED


async def validate_token(
    session: "aiohttp.ClientSession",
    key_name: str,
    access_token: str
) -> KeyValidationResult:
    """
    Validate a single API token.

    Calls /me to verify token validity and get user info.
    Calls /me/permissions to verify required permissions.
    """
    try:
        # Call /me
        async with session.get(
            f"{GRAPH_API_BASE}/me",
            params={
                "access_token": access_token,
                "fields": "id,name"
            }
        ) as resp:
            if resp.status != 200:
                error_data = await resp.json()
                return KeyValidationResult(
                    key_name=key_name,
                    status=PreflightStatus.FAILED,
                    error=error_data.get("error", {}).get("message", "Unknown error")
                )

            user_data = await resp.json()

        # Call /me/permissions
        async with session.get(
            f"{GRAPH_API_BASE}/me/permissions",
            params={"access_token": access_token}
        ) as resp:
            permissions = []
            if resp.status == 200:
                perm_data = await resp.json()
                permissions = [
                    p["permission"] for p in perm_data.get("data", [])
                    if p.get("status") == "granted"
                ]

        # Check for required permissions
        required = ["ads_read"]
        missing = [p for p in required if p not in permissions]

        if missing:
            return KeyValidationResult(
                key_name=key_name,
                status=PreflightStatus.WARNING,
                user_id=user_data.get("id"),
                user_name=user_data.get("name"),
                permissions=permissions,
                error=f"Missing permissions: {missing}"
            )

        return KeyValidationResult(
            key_name=key_name,
            status=PreflightStatus.PASSED,
            user_id=user_data.get("id"),
            user_name=user_data.get("name"),
            permissions=permissions
        )

    except Exception as e:
        return KeyValidationResult(
            key_name=key_name,
            status=PreflightStatus.FAILED,
            error=str(e)
        )


async def validate_account(
    session: "aiohttp.ClientSession",
    account_name: str,
    account_id: str,
    access_token: str
) -> AccountValidationResult:
    """
    Validate access to a single ad account.

    Calls /act_{id} to verify account accessibility.
    """
    try:
        async with session.get(
            f"{GRAPH_API_BASE}/{account_id}",
            params={
                "access_token": access_token,
                "fields": "id,name,account_status,business"
            }
        ) as resp:
            if resp.status != 200:
                error_data = await resp.json()
                return AccountValidationResult(
                    account_name=account_name,
                    status=PreflightStatus.FAILED,
                    error=error_data.get("error", {}).get("message", "Unknown error")
                )

            account_data = await resp.json()

        # Map account_status codes
        status_map = {
            1: "ACTIVE",
            2: "DISABLED",
            3: "UNSETTLED",
            7: "PENDING_RISK_REVIEW",
            8: "PENDING_SETTLEMENT",
            9: "IN_GRACE_PERIOD",
            100: "PENDING_CLOSURE",
            101: "CLOSED",
            201: "ANY_ACTIVE",
            202: "ANY_CLOSED"
        }

        account_status = account_data.get("account_status", 0)
        status_str = status_map.get(account_status, f"UNKNOWN({account_status})")

        # Non-active statuses are warnings
        if account_status != 1:
            return AccountValidationResult(
                account_name=account_name,
                status=PreflightStatus.WARNING,
                account_id=account_data.get("id"),
                account_status=status_str,
                business_name=account_data.get("business", {}).get("name"),
                error=f"Account status is {status_str}, not ACTIVE"
            )

        return AccountValidationResult(
            account_name=account_name,
            status=PreflightStatus.PASSED,
            account_id=account_data.get("id"),
            account_status=status_str,
            business_name=account_data.get("business", {}).get("name")
        )

    except Exception as e:
        return AccountValidationResult(
            account_name=account_name,
            status=PreflightStatus.FAILED,
            error=str(e)
        )


async def run_preflight_checks(credential_manager: "CredentialManager") -> PreflightResult:
    """
    Run all preflight validation checks.

    Args:
        credential_manager: Initialized CredentialManager instance

    Returns:
        PreflightResult with all validation results
    """
    if not AIOHTTP_AVAILABLE:
        return PreflightResult(
            status=PreflightStatus.WARNING,
            warnings=["aiohttp not installed, skipping preflight checks"]
        )

    key_results: List[KeyValidationResult] = []
    account_results: List[AccountValidationResult] = []
    warnings: List[str] = []
    errors: List[str] = []

    async with aiohttp.ClientSession() as session:
        # Validate all API keys in parallel
        key_tasks = [
            validate_token(session, key.name, key.access_token)
            for key in credential_manager.api_keys.values()
        ]
        if key_tasks:
            key_results = await asyncio.gather(*key_tasks)

        # Collect key errors
        for result in key_results:
            if result.status == PreflightStatus.FAILED:
                errors.append(f"Key '{result.key_name}': {result.error}")
            elif result.status == PreflightStatus.WARNING:
                warnings.append(f"Key '{result.key_name}': {result.error}")

        # Only validate accounts for keys that passed
        valid_keys = {r.key_name for r in key_results if r.status != PreflightStatus.FAILED}

        account_tasks = []
        for acc in credential_manager.accounts.values():
            if acc.api_key in valid_keys:
                token = credential_manager.get_token_for_account(acc.name)
                account_tasks.append(
                    validate_account(session, acc.name, acc.ad_account_id, token)
                )
            else:
                # Skip accounts with failed keys
                account_results.append(AccountValidationResult(
                    account_name=acc.name,
                    status=PreflightStatus.FAILED,
                    error=f"API key '{acc.api_key}' failed validation"
                ))

        if account_tasks:
            account_results.extend(await asyncio.gather(*account_tasks))

        # Collect account errors
        for result in account_results:
            if result.status == PreflightStatus.FAILED:
                errors.append(f"Account '{result.account_name}': {result.error}")
            elif result.status == PreflightStatus.WARNING:
                warnings.append(f"Account '{result.account_name}': {result.error}")

    # Determine overall status
    if errors:
        overall_status = PreflightStatus.FAILED
    elif warnings:
        overall_status = PreflightStatus.WARNING
    else:
        overall_status = PreflightStatus.PASSED

    return PreflightResult(
        status=overall_status,
        keys=list(key_results),
        accounts=account_results,
        warnings=warnings,
        errors=errors
    )


def format_preflight_result(result: PreflightResult) -> str:
    """Format preflight result for display."""
    lines = []

    # Header
    status_indicator = {
        PreflightStatus.PASSED: "[PASSED]",
        PreflightStatus.WARNING: "[WARNING]",
        PreflightStatus.FAILED: "[FAILED]"
    }
    lines.append(f"{status_indicator[result.status]} Preflight Check: {result.status.value.upper()}")
    lines.append("")

    # Keys
    if result.keys:
        lines.append("API Keys:")
        for key in result.keys:
            indicator = status_indicator[key.status]
            if key.status == PreflightStatus.PASSED:
                lines.append(f"  {indicator} {key.key_name}: OK (user: {key.user_name})")
            else:
                lines.append(f"  {indicator} {key.key_name}: {key.error}")
        lines.append("")

    # Accounts
    if result.accounts:
        lines.append("Accounts:")
        for acc in result.accounts:
            indicator = status_indicator[acc.status]
            if acc.status == PreflightStatus.PASSED:
                lines.append(
                    f"  {indicator} {acc.account_name}: OK "
                    f"({acc.account_id}, {acc.account_status})"
                )
            else:
                lines.append(f"  {indicator} {acc.account_name}: {acc.error}")

    # Summary
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  [ERROR] {error}")

    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  [WARN] {warning}")

    return "\n".join(lines)
