"""
Multi-tenant credential manager for Meta Ads MCP.

Handles:
- Loading and validating credentials.json
- Token routing (account → API key)
- Session-based account switching
- Token expiration monitoring
"""

import json
import os
import pathlib
import platform
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CredentialError(Exception):
    """Base exception for credential errors."""
    pass


class AccountNotFoundError(CredentialError):
    """Raised when account_name doesn't exist."""
    pass


class KeyNotFoundError(CredentialError):
    """Raised when api_key reference is invalid."""
    pass


class TokenExpiredError(CredentialError):
    """Raised when token has expired."""
    pass


class ValidationError(CredentialError):
    """Raised when credentials.json is invalid."""
    pass


@dataclass
class ApiKeyConfig:
    """Configuration for a single API key."""
    name: str
    access_token: str
    business_manager_id: str
    app_id: str = ""
    expires_at: Optional[datetime] = None
    tier: str = "standard"  # "development" or "standard"

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    @property
    def days_until_expiry(self) -> Optional[int]:
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)


@dataclass
class AccountConfig:
    """Configuration for a single ad account."""
    name: str
    display_name: str
    ad_account_id: str
    api_key: str  # Reference to ApiKeyConfig.name


@dataclass
class CredentialManagerState:
    """Runtime state for credential manager."""
    current_account: Optional[str] = None
    preflight_passed: bool = False
    preflight_errors: List[str] = field(default_factory=list)


class CredentialManager:
    """
    Multi-tenant credential manager.

    Singleton instance manages all credential operations.
    """

    _instance: Optional['CredentialManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.api_keys: Dict[str, ApiKeyConfig] = {}
        self.accounts: Dict[str, AccountConfig] = {}
        self.default_account: Optional[str] = None
        self._state = CredentialManagerState()
        self._initialized = True

        # Try to load credentials
        self._load_credentials()

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    # === Path Resolution ===

    def _get_credentials_path(self) -> pathlib.Path:
        """Get platform-specific credentials.json path."""
        if platform.system() == "Windows":
            base_path = pathlib.Path(os.environ.get("APPDATA", ""))
        elif platform.system() == "Darwin":
            base_path = pathlib.Path.home() / "Library" / "Application Support"
        else:
            base_path = pathlib.Path.home() / ".config"
        return base_path / "meta-ads-mcp" / "credentials.json"

    # === Loading & Validation ===

    def _load_credentials(self):
        """Load credentials from JSON file or fall back to .env."""
        cred_path = self._get_credentials_path()

        if cred_path.exists():
            self._load_from_json(cred_path)
        else:
            self._load_from_env()

    def _load_from_json(self, path: pathlib.Path):
        """Load and validate credentials.json."""
        try:
            with open(path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in credentials.json: {e}")

        # Validate version
        version = data.get("version")
        if version != 2:
            raise ValidationError(
                f"Unsupported credentials version: {version}. Expected: 2"
            )

        # Load API keys
        for key_name, key_data in data.get("api_keys", {}).items():
            expires_at = None
            if "expires_at" in key_data:
                try:
                    expires_at = datetime.fromisoformat(
                        key_data["expires_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    logger.warning(f"Invalid expires_at for key {key_name}")

            self.api_keys[key_name] = ApiKeyConfig(
                name=key_name,
                access_token=key_data["access_token"],
                business_manager_id=key_data.get("business_manager_id", ""),
                app_id=key_data.get("app_id", ""),
                expires_at=expires_at,
                tier=key_data.get("tier", "standard")
            )

        # Load accounts
        for acc_name, acc_data in data.get("accounts", {}).items():
            # Validate api_key reference
            api_key_ref = acc_data["api_key"]
            if api_key_ref not in self.api_keys:
                raise ValidationError(
                    f"Account '{acc_name}' references unknown api_key '{api_key_ref}'"
                )

            self.accounts[acc_name] = AccountConfig(
                name=acc_name,
                display_name=acc_data["display_name"],
                ad_account_id=acc_data["ad_account_id"],
                api_key=api_key_ref
            )

        # Set default account
        self.default_account = data.get("default_account")
        if self.default_account and self.default_account not in self.accounts:
            raise ValidationError(
                f"default_account '{self.default_account}' not found in accounts"
            )

        self._state.current_account = self.default_account

        # Validate unique constraints
        self._validate_unique_constraints()

        logger.info(
            f"Loaded {len(self.api_keys)} API keys and "
            f"{len(self.accounts)} accounts from credentials.json"
        )

    def _load_from_env(self):
        """Backward compatibility: load single account from .env."""
        token = os.environ.get("META_ACCESS_TOKEN")
        account_id = os.environ.get("META_AD_ACCOUNT_ID")
        app_id = os.environ.get("META_APP_ID", "")

        if token and account_id:
            self.api_keys["default"] = ApiKeyConfig(
                name="default",
                access_token=token,
                business_manager_id="",
                app_id=app_id,
                tier="standard"
            )
            self.accounts["default"] = AccountConfig(
                name="default",
                display_name="Default Account",
                ad_account_id=account_id,
                api_key="default"
            )
            self.default_account = "default"
            self._state.current_account = "default"

            logger.info("Loaded credentials from .env (legacy mode)")
        else:
            logger.warning(
                "No credentials found. Create credentials.json or set "
                "META_ACCESS_TOKEN and META_AD_ACCOUNT_ID environment variables."
            )

    def _validate_unique_constraints(self):
        """Validate no duplicate tokens or account IDs."""
        # Check duplicate access tokens
        tokens = [k.access_token for k in self.api_keys.values()]
        if len(tokens) != len(set(tokens)):
            raise ValidationError("Duplicate access_token found in api_keys")

        # Check duplicate ad account IDs
        account_ids = [a.ad_account_id for a in self.accounts.values()]
        if len(account_ids) != len(set(account_ids)):
            raise ValidationError("Duplicate ad_account_id found in accounts")

    # === Token Routing ===

    def get_token_for_account(self, account_name: Optional[str] = None) -> str:
        """
        Get the API access token for a specific account.

        Args:
            account_name: Account name, or None for current account

        Returns:
            Access token string

        Raises:
            AccountNotFoundError: If account doesn't exist
            KeyNotFoundError: If api_key reference is invalid
            TokenExpiredError: If token has expired
        """
        # Resolve account name
        name = account_name or self._state.current_account
        if not name:
            raise AccountNotFoundError(
                "No account specified and no default account set"
            )

        account = self.accounts.get(name)
        if not account:
            raise AccountNotFoundError(
                f"Account '{name}' not found. "
                f"Available: {list(self.accounts.keys())}"
            )

        api_key = self.api_keys.get(account.api_key)
        if not api_key:
            raise KeyNotFoundError(
                f"API key '{account.api_key}' not found for account '{name}'"
            )

        # Check expiration
        if api_key.is_expired:
            raise TokenExpiredError(
                f"Token for key '{api_key.name}' expired on {api_key.expires_at}"
            )

        return api_key.access_token

    def get_account_id(self, account_name: Optional[str] = None) -> str:
        """Get the ad account ID for a specific account."""
        name = account_name or self._state.current_account
        if not name:
            raise AccountNotFoundError(
                "No account specified and no default account set"
            )

        account = self.accounts.get(name)
        if not account:
            raise AccountNotFoundError(f"Account '{name}' not found")

        return account.ad_account_id

    def get_key_for_account(self, account_name: Optional[str] = None) -> ApiKeyConfig:
        """Get the API key config for a specific account."""
        name = account_name or self._state.current_account
        if not name:
            raise AccountNotFoundError(
                "No account specified and no default account set"
            )

        account = self.accounts.get(name)
        if not account:
            raise AccountNotFoundError(f"Account '{name}' not found")

        return self.api_keys[account.api_key]

    # === Account Management ===

    def get_current_account(self) -> Optional[str]:
        """Get the currently active account name."""
        return self._state.current_account

    def set_current_account(self, account_name: str) -> bool:
        """
        Set the current active account (session-based).

        Args:
            account_name: Name of account to switch to

        Returns:
            True if successful, False if account not found
        """
        if account_name not in self.accounts:
            return False
        self._state.current_account = account_name
        return True

    def list_accounts(self) -> List[Dict]:
        """List all configured accounts with metadata."""
        result = []
        for acc in self.accounts.values():
            key = self.api_keys.get(acc.api_key)
            result.append({
                "name": acc.name,
                "display_name": acc.display_name,
                "ad_account_id": acc.ad_account_id,
                "api_key": acc.api_key,
                "key_tier": key.tier if key else "unknown",
                "key_expires_in_days": key.days_until_expiry if key else None,
                "is_current": acc.name == self._state.current_account
            })
        return result

    def list_api_keys(self) -> List[Dict]:
        """List all API keys with metadata."""
        result = []
        for key in self.api_keys.values():
            accounts_using = [
                a.name for a in self.accounts.values()
                if a.api_key == key.name
            ]
            result.append({
                "name": key.name,
                "business_manager_id": key.business_manager_id,
                "tier": key.tier,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "days_until_expiry": key.days_until_expiry,
                "is_expired": key.is_expired,
                "accounts": accounts_using
            })
        return result

    # === Token Expiration Monitoring ===

    def get_expiring_tokens(self, days_threshold: int = 7) -> List[Dict]:
        """
        Get tokens expiring within the threshold.

        Args:
            days_threshold: Alert if expiring within this many days

        Returns:
            List of keys with expiration info
        """
        expiring = []
        for key in self.api_keys.values():
            if key.days_until_expiry is not None:
                if key.days_until_expiry <= days_threshold:
                    expiring.append({
                        "key_name": key.name,
                        "expires_at": key.expires_at.isoformat(),
                        "days_remaining": key.days_until_expiry,
                        "accounts_affected": [
                            a.name for a in self.accounts.values()
                            if a.api_key == key.name
                        ]
                    })
        return expiring

    def check_token_expiration_alerts(self) -> Optional[str]:
        """
        Check for token expiration and return alert message if any.

        Returns:
            Alert message string, or None if no alerts
        """
        expiring = self.get_expiring_tokens(days_threshold=7)
        if not expiring:
            return None

        alerts = []
        for item in expiring:
            if item["days_remaining"] == 0:
                alerts.append(
                    f"CRITICAL: Token '{item['key_name']}' EXPIRES TODAY! "
                    f"Accounts affected: {', '.join(item['accounts_affected'])}"
                )
            else:
                alerts.append(
                    f"WARNING: Token '{item['key_name']}' expires in "
                    f"{item['days_remaining']} days. "
                    f"Accounts affected: {', '.join(item['accounts_affected'])}"
                )

        return "\n".join(alerts)


# Singleton instance - lazy initialization
def get_credential_manager() -> CredentialManager:
    """Get the singleton CredentialManager instance."""
    return CredentialManager()
