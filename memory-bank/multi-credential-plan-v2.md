# Multi-Credential Architecture Plan v2

**Created:** 2026-01-22
**Status:** Planned
**Supersedes:** windows-install-multi-credential-plan.md (Parts 2 & 4)

---

## Executive Summary

Support **3 API keys** from **3 separate Business Managers** accessing **10 ad accounts** with proper rate limiting, startup validation, and token expiration alerting.

### Scope Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Failover | Hard error, no auto-failover | Simpler, user controls retry |
| Read/Write | Read-only (`ads_read` scope) | No write operations needed now |
| Security | Basic (plaintext JSON) | Solo use, no client isolation needed |
| Response optimization | Not critical path | Claude Code handles large responses |
| Token refresh | Manual with alerting | System user tokens, 60-day expiry |

### Out of Scope (for now)

- Auto-failover between keys
- Write operations (`ads_management`)
- OAuth refresh flows
- At-rest credential encryption
- Audit logging
- Compact response formats for Claude Desktop

---

## Part 1: Credential Schema v2

### File Location

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/meta-ads-mcp/credentials.json` |
| Windows | `%APPDATA%\meta-ads-mcp\credentials.json` |
| Linux | `~/.config/meta-ads-mcp/credentials.json` |

### Schema Definition

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["version", "api_keys", "accounts", "default_account"],
  "properties": {
    "version": { "const": 2 },
    "api_keys": {
      "type": "object",
      "minProperties": 1,
      "maxProperties": 3,
      "additionalProperties": {
        "type": "object",
        "required": ["access_token", "business_manager_id"],
        "properties": {
          "access_token": {
            "type": "string",
            "pattern": "^EAA",
            "description": "System user access token"
          },
          "business_manager_id": {
            "type": "string",
            "description": "BM ID that owns this token"
          },
          "app_id": {
            "type": "string",
            "description": "Meta App ID (optional)"
          },
          "expires_at": {
            "type": "string",
            "format": "date-time",
            "description": "Token expiration timestamp"
          },
          "tier": {
            "enum": ["development", "standard"],
            "default": "standard",
            "description": "Rate limit tier"
          }
        }
      }
    },
    "accounts": {
      "type": "object",
      "minProperties": 1,
      "maxProperties": 10,
      "additionalProperties": {
        "type": "object",
        "required": ["display_name", "ad_account_id", "api_key"],
        "properties": {
          "display_name": { "type": "string" },
          "ad_account_id": {
            "type": "string",
            "pattern": "^act_[0-9]+$"
          },
          "api_key": {
            "type": "string",
            "description": "Reference to api_keys entry"
          }
        }
      }
    },
    "default_account": {
      "type": "string",
      "description": "Account name to use when none specified"
    }
  }
}
```

### Example Configuration

```json
{
  "version": 2,
  "api_keys": {
    "bm_agency_1": {
      "access_token": "EAAxxxxx...",
      "business_manager_id": "1234567890",
      "app_id": "111111111",
      "expires_at": "2026-03-22T00:00:00Z",
      "tier": "standard"
    },
    "bm_agency_2": {
      "access_token": "EAAyyyyy...",
      "business_manager_id": "2345678901",
      "app_id": "222222222",
      "expires_at": "2026-03-22T00:00:00Z",
      "tier": "standard"
    },
    "bm_personal": {
      "access_token": "EAAzzzzz...",
      "business_manager_id": "3456789012",
      "app_id": "333333333",
      "expires_at": "2026-03-22T00:00:00Z",
      "tier": "development"
    }
  },
  "accounts": {
    "client_alpha": {
      "display_name": "Client Alpha Ads",
      "ad_account_id": "act_111111111",
      "api_key": "bm_agency_1"
    },
    "client_beta": {
      "display_name": "Client Beta Ads",
      "ad_account_id": "act_222222222",
      "api_key": "bm_agency_1"
    },
    "client_gamma": {
      "display_name": "Client Gamma Ads",
      "ad_account_id": "act_333333333",
      "api_key": "bm_agency_1"
    },
    "client_delta": {
      "display_name": "Client Delta Ads",
      "ad_account_id": "act_444444444",
      "api_key": "bm_agency_2"
    },
    "client_epsilon": {
      "display_name": "Client Epsilon Ads",
      "ad_account_id": "act_555555555",
      "api_key": "bm_agency_2"
    },
    "client_zeta": {
      "display_name": "Client Zeta Ads",
      "ad_account_id": "act_666666666",
      "api_key": "bm_agency_2"
    },
    "client_eta": {
      "display_name": "Client Eta Ads",
      "ad_account_id": "act_777777777",
      "api_key": "bm_agency_2"
    },
    "personal_1": {
      "display_name": "Personal Account 1",
      "ad_account_id": "act_888888888",
      "api_key": "bm_personal"
    },
    "personal_2": {
      "display_name": "Personal Account 2",
      "ad_account_id": "act_999999999",
      "api_key": "bm_personal"
    },
    "personal_3": {
      "display_name": "Personal Account 3",
      "ad_account_id": "act_000000000",
      "api_key": "bm_personal"
    }
  },
  "default_account": "client_alpha"
}
```

### Validation Rules

1. **Unique constraints:**
   - No duplicate `ad_account_id` across accounts
   - No duplicate `access_token` across api_keys
   - All `api_key` references must exist in `api_keys`
   - `default_account` must exist in `accounts`

2. **Consistency checks:**
   - Each account's `api_key` must be a valid key that can access it
   - Token format must start with `EAA`
   - Account ID format must be `act_` + digits

---

## Part 2: Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Server Startup                           │
│                                                                      │
│  1. Load credentials.json                                            │
│  2. Validate schema                                                  │
│  3. Run preflight checks (token validity, account access)            │
│  4. Initialize rate limiter per key                                  │
│  5. Start token expiration monitor                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Request Flow                                  │
│                                                                      │
│  Tool called with account_name="client_alpha"                        │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                 │
│  │ CredentialManager│                                                │
│  │                  │                                                │
│  │ 1. Resolve account → api_key mapping                              │
│  │ 2. Check rate limit for key                                       │
│  │ 3. Return token + account_id                                      │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                 │
│  │   RateLimiter   │                                                 │
│  │                 │                                                 │
│  │ • Check if key is blocked                                         │
│  │ • If blocked → raise RateLimitError                               │
│  │ • If OK → record call, return                                     │
│  └────────┬─────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                 │
│  │  Meta API Call  │                                                 │
│  │                 │                                                 │
│  │ • Make request with token                                         │
│  │ • On success → record in rate limiter                             │
│  │ • On error → classify and handle                                  │
│  └─────────────────┘                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### File Structure

```
meta_ads_mcp/
├── core/
│   ├── __init__.py
│   ├── server.py          # Existing - add startup hooks
│   ├── auth.py            # Modify - use credential_manager
│   ├── api.py             # Modify - add rate limit recording
│   ├── credentials.py     # NEW - credential manager
│   ├── rate_limiter.py    # NEW - per-key rate limiting
│   ├── preflight.py       # NEW - startup validation
│   ├── errors.py          # NEW - error classification
│   ├── accounts.py        # Modify - add account_name param
│   ├── campaigns.py       # Modify - add account_name param
│   ├── adsets.py          # Modify - add account_name param
│   ├── ads.py             # Modify - add account_name param
│   ├── insights.py        # Modify - add account_name param
│   └── targeting.py       # Modify - add account_name param
```

---

## Part 3: Core Components

### 3.1 Credential Manager (`credentials.py`)

```python
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
from datetime import datetime, timedelta
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
                    f"⚠️ CRITICAL: Token '{item['key_name']}' EXPIRES TODAY! "
                    f"Accounts affected: {', '.join(item['accounts_affected'])}"
                )
            else:
                alerts.append(
                    f"⚠️ WARNING: Token '{item['key_name']}' expires in "
                    f"{item['days_remaining']} days. "
                    f"Accounts affected: {', '.join(item['accounts_affected'])}"
                )

        return "\n".join(alerts)


# Singleton instance
credential_manager = CredentialManager()
```

### 3.2 Rate Limiter (`rate_limiter.py`)

```python
"""
Per-key rate limiter for Meta Graph API.

Implements Meta's rate limiting model:
- Score-based system with exponential decay
- Different tiers (development vs standard)
- Per-key tracking (not per-account, since accounts share keys)
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RateLimitTier(Enum):
    DEVELOPMENT = "development"
    STANDARD = "standard"


@dataclass
class TierConfig:
    """Rate limit configuration per tier."""
    max_score: int
    decay_rate: float  # Points decayed per second
    block_duration_seconds: int
    call_cost: int = 1  # Read operations cost


TIER_CONFIGS = {
    RateLimitTier.DEVELOPMENT: TierConfig(
        max_score=60,
        decay_rate=60 / 300,  # 60 points over 5 minutes = 0.2/sec
        block_duration_seconds=300,  # 5 minutes
        call_cost=1
    ),
    RateLimitTier.STANDARD: TierConfig(
        max_score=9000,
        decay_rate=9000 / 300,  # 9000 points over 5 minutes = 30/sec
        block_duration_seconds=60,  # 1 minute
        call_cost=1
    )
}


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, key_name: str, retry_after_seconds: int):
        self.key_name = key_name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limit exceeded for key '{key_name}'. "
            f"Retry after {retry_after_seconds} seconds."
        )


@dataclass
class KeyRateLimitState:
    """Track rate limit state for a single API key."""
    key_name: str
    tier: RateLimitTier
    current_score: float = 0.0
    last_update: float = field(default_factory=time.time)
    blocked_until: Optional[float] = None
    total_calls: int = 0

    @property
    def is_blocked(self) -> bool:
        if self.blocked_until is None:
            return False
        return time.time() < self.blocked_until

    @property
    def block_time_remaining(self) -> int:
        if self.blocked_until is None:
            return 0
        remaining = self.blocked_until - time.time()
        return max(0, int(remaining))


class RateLimiter:
    """
    Per-key rate limiter with exponential decay.

    Thread-safe singleton for tracking API usage across all keys.
    """

    _instance: Optional['RateLimiter'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._states: Dict[str, KeyRateLimitState] = {}
        self._lock = threading.Lock()
        self._initialized = True

    def _get_or_create_state(
        self,
        key_name: str,
        tier: str = "standard"
    ) -> KeyRateLimitState:
        """Get or create state for a key."""
        if key_name not in self._states:
            tier_enum = RateLimitTier(tier)
            self._states[key_name] = KeyRateLimitState(
                key_name=key_name,
                tier=tier_enum
            )
        return self._states[key_name]

    def _apply_decay(self, state: KeyRateLimitState):
        """Apply time-based decay to the score."""
        now = time.time()
        elapsed = now - state.last_update
        config = TIER_CONFIGS[state.tier]

        # Decay the score
        decay_amount = elapsed * config.decay_rate
        state.current_score = max(0, state.current_score - decay_amount)
        state.last_update = now

    def check_rate_limit(self, key_name: str, tier: str = "standard") -> bool:
        """
        Check if a request is allowed for this key.

        Args:
            key_name: The API key identifier
            tier: Rate limit tier ("development" or "standard")

        Returns:
            True if request allowed

        Raises:
            RateLimitError: If rate limited
        """
        with self._lock:
            state = self._get_or_create_state(key_name, tier)

            # Check if blocked
            if state.is_blocked:
                raise RateLimitError(key_name, state.block_time_remaining)

            # Apply decay
            self._apply_decay(state)

            # Check if would exceed limit
            config = TIER_CONFIGS[state.tier]
            if state.current_score + config.call_cost > config.max_score:
                # Block the key
                state.blocked_until = time.time() + config.block_duration_seconds
                raise RateLimitError(key_name, config.block_duration_seconds)

            return True

    def record_call(self, key_name: str, tier: str = "standard"):
        """
        Record an API call for rate limiting.

        Call this AFTER a successful API request.
        """
        with self._lock:
            state = self._get_or_create_state(key_name, tier)
            config = TIER_CONFIGS[state.tier]

            state.current_score += config.call_cost
            state.total_calls += 1
            state.last_update = time.time()

            logger.debug(
                f"Rate limiter: key={key_name}, score={state.current_score:.1f}/"
                f"{config.max_score}, calls={state.total_calls}"
            )

    def record_rate_limit_error(self, key_name: str, retry_after: Optional[int] = None):
        """
        Record when Meta returns a rate limit error.

        This blocks the key for the specified duration.
        """
        with self._lock:
            state = self._get_or_create_state(key_name)
            config = TIER_CONFIGS[state.tier]

            block_duration = retry_after or config.block_duration_seconds
            state.blocked_until = time.time() + block_duration

            logger.warning(
                f"Rate limit hit for key '{key_name}', blocked for {block_duration}s"
            )

    def get_key_status(self, key_name: str) -> Dict:
        """Get current rate limit status for a key."""
        with self._lock:
            if key_name not in self._states:
                return {
                    "key_name": key_name,
                    "status": "unknown",
                    "message": "No calls recorded yet"
                }

            state = self._states[key_name]
            self._apply_decay(state)
            config = TIER_CONFIGS[state.tier]

            usage_percent = (state.current_score / config.max_score) * 100

            return {
                "key_name": key_name,
                "tier": state.tier.value,
                "current_score": round(state.current_score, 1),
                "max_score": config.max_score,
                "usage_percent": round(usage_percent, 1),
                "is_blocked": state.is_blocked,
                "block_time_remaining": state.block_time_remaining,
                "total_calls": state.total_calls,
                "status": "blocked" if state.is_blocked else (
                    "warning" if usage_percent > 80 else "ok"
                )
            }

    def get_all_status(self) -> Dict[str, Dict]:
        """Get rate limit status for all keys."""
        with self._lock:
            return {
                key_name: self.get_key_status(key_name)
                for key_name in self._states
            }

    def reset_key(self, key_name: str):
        """Reset rate limit state for a key (for testing)."""
        with self._lock:
            if key_name in self._states:
                del self._states[key_name]


# Singleton instance
rate_limiter = RateLimiter()
```

### 3.3 Preflight Validation (`preflight.py`)

```python
"""
Startup preflight checks for credentials validation.

Validates:
- Token validity (can call /me)
- Account accessibility (can call /act_{id})
- Permission verification (has ads_read)
"""

import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import logging

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
    permissions: List[str] = None
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
    keys: List[KeyValidationResult]
    accounts: List[AccountValidationResult]
    warnings: List[str]
    errors: List[str]

    @property
    def passed(self) -> bool:
        return self.status == PreflightStatus.PASSED


async def validate_token(
    session: aiohttp.ClientSession,
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
    session: aiohttp.ClientSession,
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


async def run_preflight_checks(credential_manager) -> PreflightResult:
    """
    Run all preflight validation checks.

    Args:
        credential_manager: Initialized CredentialManager instance

    Returns:
        PreflightResult with all validation results
    """
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
        keys=key_results,
        accounts=account_results,
        warnings=warnings,
        errors=errors
    )


def format_preflight_result(result: PreflightResult) -> str:
    """Format preflight result for display."""
    lines = []

    # Header
    status_emoji = {
        PreflightStatus.PASSED: "✅",
        PreflightStatus.WARNING: "⚠️",
        PreflightStatus.FAILED: "❌"
    }
    lines.append(f"{status_emoji[result.status]} Preflight Check: {result.status.value.upper()}")
    lines.append("")

    # Keys
    lines.append("API Keys:")
    for key in result.keys:
        emoji = status_emoji[key.status]
        if key.status == PreflightStatus.PASSED:
            lines.append(f"  {emoji} {key.key_name}: OK (user: {key.user_name})")
        else:
            lines.append(f"  {emoji} {key.key_name}: {key.error}")
    lines.append("")

    # Accounts
    lines.append("Accounts:")
    for acc in result.accounts:
        emoji = status_emoji[acc.status]
        if acc.status == PreflightStatus.PASSED:
            lines.append(
                f"  {emoji} {acc.account_name}: OK "
                f"({acc.account_id}, {acc.account_status})"
            )
        else:
            lines.append(f"  {emoji} {acc.account_name}: {acc.error}")

    # Summary
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  ❌ {error}")

    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  ⚠️ {warning}")

    return "\n".join(lines)
```

### 3.4 Error Classification (`errors.py`)

```python
"""
Meta Graph API error classification and handling.

Maps Meta error codes to appropriate actions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorAction(Enum):
    """Action to take for an error."""
    RETRY = "retry"           # Retry with backoff
    RATE_LIMIT = "rate_limit" # Record rate limit, block key temporarily
    AUTH_ERROR = "auth_error" # Token invalid, don't retry
    PERM_ERROR = "perm_error" # Permission denied, don't retry
    NOT_FOUND = "not_found"   # Resource doesn't exist
    BAD_REQUEST = "bad_req"   # Invalid parameters
    SERVER_ERROR = "server"   # Meta server error, retry
    UNKNOWN = "unknown"       # Unknown error


@dataclass
class ErrorClassification:
    """Classification of a Meta API error."""
    code: int
    subcode: Optional[int]
    action: ErrorAction
    retryable: bool
    max_retries: int
    description: str


# Meta Graph API error code mapping
# Reference: https://developers.facebook.com/docs/graph-api/guides/error-handling
ERROR_MAP = {
    # OAuth errors (190.xxx)
    190: ErrorClassification(
        code=190,
        subcode=None,
        action=ErrorAction.AUTH_ERROR,
        retryable=False,
        max_retries=0,
        description="Invalid OAuth access token"
    ),

    # Rate limiting errors
    4: ErrorClassification(
        code=4,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=3,
        description="Application request limit reached"
    ),
    17: ErrorClassification(
        code=17,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=3,
        description="User request limit reached"
    ),
    32: ErrorClassification(
        code=32,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=2,
        description="Page request limit reached"
    ),
    613: ErrorClassification(
        code=613,
        subcode=None,
        action=ErrorAction.RATE_LIMIT,
        retryable=True,
        max_retries=2,
        description="Calls to this API have exceeded the rate limit"
    ),

    # Permission errors
    10: ErrorClassification(
        code=10,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="Permission denied"
    ),
    200: ErrorClassification(
        code=200,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="Permission error (requires extended permission)"
    ),
    294: ErrorClassification(
        code=294,
        subcode=None,
        action=ErrorAction.PERM_ERROR,
        retryable=False,
        max_retries=0,
        description="App not whitelisted"
    ),

    # Not found
    100: ErrorClassification(
        code=100,
        subcode=None,
        action=ErrorAction.BAD_REQUEST,
        retryable=False,
        max_retries=0,
        description="Invalid parameter"
    ),

    # Server errors
    1: ErrorClassification(
        code=1,
        subcode=None,
        action=ErrorAction.SERVER_ERROR,
        retryable=True,
        max_retries=3,
        description="Unknown error (Meta server issue)"
    ),
    2: ErrorClassification(
        code=2,
        subcode=None,
        action=ErrorAction.SERVER_ERROR,
        retryable=True,
        max_retries=3,
        description="Service temporarily unavailable"
    ),
}


def classify_error(error_code: int, error_subcode: Optional[int] = None) -> ErrorClassification:
    """
    Classify a Meta API error.

    Args:
        error_code: The error code from Meta's response
        error_subcode: Optional subcode for more specific errors

    Returns:
        ErrorClassification with action and retry info
    """
    # Check for exact match
    if error_code in ERROR_MAP:
        return ERROR_MAP[error_code]

    # Default classification
    return ErrorClassification(
        code=error_code,
        subcode=error_subcode,
        action=ErrorAction.UNKNOWN,
        retryable=False,
        max_retries=0,
        description=f"Unknown error code: {error_code}"
    )


class MetaApiError(Exception):
    """Exception for Meta API errors with classification."""

    def __init__(
        self,
        message: str,
        error_code: int,
        error_subcode: Optional[int] = None,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.retry_after = retry_after
        self.classification = classify_error(error_code, error_subcode)
        super().__init__(message)

    @property
    def is_retryable(self) -> bool:
        return self.classification.retryable

    @property
    def action(self) -> ErrorAction:
        return self.classification.action

    @property
    def max_retries(self) -> int:
        return self.classification.max_retries
```

---

## Part 4: Integration

### 4.1 Modify `auth.py`

```python
# Add to existing auth.py

from .credentials import credential_manager, AccountNotFoundError, TokenExpiredError


def get_access_token_for_account(account_name: Optional[str] = None) -> str:
    """
    Get access token for the specified or current account.

    This replaces direct ENV lookups for multi-tenant support.
    """
    return credential_manager.get_token_for_account(account_name)


def get_ad_account_id_for_account(account_name: Optional[str] = None) -> str:
    """Get ad account ID for the specified or current account."""
    return credential_manager.get_account_id(account_name)
```

### 4.2 Modify `api.py` Decorator

```python
# Update meta_api_tool decorator in api.py

from .credentials import credential_manager
from .rate_limiter import rate_limiter, RateLimitError
from .errors import MetaApiError, ErrorAction

def meta_api_tool(func):
    """
    Decorator for Meta API tool functions.

    Handles:
    - Token resolution from account_name
    - Rate limit checking and recording
    - Error classification
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract account_name from kwargs
        account_name = kwargs.get("account_name")

        # Get the API key for this account
        try:
            key_config = credential_manager.get_key_for_account(account_name)
        except AccountNotFoundError as e:
            return json.dumps({"error": str(e)})

        # Check rate limit BEFORE making the call
        try:
            rate_limiter.check_rate_limit(key_config.name, key_config.tier)
        except RateLimitError as e:
            return json.dumps({
                "error": "Rate limit exceeded",
                "key": e.key_name,
                "retry_after_seconds": e.retry_after_seconds
            })

        try:
            # Call the actual function
            result = await func(*args, **kwargs)

            # Record successful call
            rate_limiter.record_call(key_config.name, key_config.tier)

            return result

        except MetaApiError as e:
            # Handle rate limit errors from Meta
            if e.action == ErrorAction.RATE_LIMIT:
                rate_limiter.record_rate_limit_error(
                    key_config.name,
                    e.retry_after
                )

            return json.dumps({
                "error": e.message,
                "error_code": e.error_code,
                "action": e.action.value,
                "retryable": e.is_retryable
            })

    return wrapper
```

### 4.3 Update Tool Signatures

All existing tools need `account_name: Optional[str] = None` parameter:

```python
# Example: campaigns.py

@mcp_server.tool()
@meta_api_tool
async def get_campaigns(
    account_id: str,
    account_name: Optional[str] = None,  # NEW
    time_range: Union[str, Dict[str, str]] = "last_30d",
    only_with_spend: bool = False,
    access_token: Optional[str] = None,
    limit: int = 25,
    after: str = ""
) -> str:
    """
    Get campaigns for an ad account.

    Args:
        account_id: The ad account ID (act_xxxxx)
        account_name: Named account from credentials.json (optional)
        ...
    """
    # If account_name provided, get account_id from credentials
    if account_name:
        account_id = credential_manager.get_account_id(account_name)

    # Rest of function unchanged...
```

### 4.4 New MCP Tools

```python
# Add to credentials.py or new file tools_credentials.py

@mcp_server.tool()
async def list_configured_accounts() -> str:
    """
    List all configured Meta Ads accounts.

    Returns account names, display names, and current status.
    """
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

    return json.dumps(result, indent=2, default=str)


@mcp_server.tool()
async def switch_account(account_name: str) -> str:
    """
    Switch to a different configured account.

    Args:
        account_name: Name of the account to switch to
    """
    if credential_manager.set_current_account(account_name):
        account = credential_manager.accounts[account_name]
        return json.dumps({
            "success": True,
            "message": f"Switched to {account.display_name}",
            "current_account": account_name,
            "ad_account_id": account.ad_account_id
        })
    else:
        return json.dumps({
            "success": False,
            "error": f"Account '{account_name}' not found",
            "available_accounts": list(credential_manager.accounts.keys())
        })


@mcp_server.tool()
async def get_current_account() -> str:
    """Get the currently active account."""
    current = credential_manager.get_current_account()
    if not current:
        return json.dumps({"error": "No account configured"})

    account = credential_manager.accounts[current]
    key = credential_manager.get_key_for_account(current)

    return json.dumps({
        "account_name": current,
        "display_name": account.display_name,
        "ad_account_id": account.ad_account_id,
        "api_key": account.api_key,
        "key_tier": key.tier,
        "key_expires_in_days": key.days_until_expiry
    }, default=str)


@mcp_server.tool()
async def get_rate_limit_status() -> str:
    """Get current rate limit status for all API keys."""
    status = rate_limiter.get_all_status()
    return json.dumps(status, indent=2)


@mcp_server.tool()
async def validate_credentials() -> str:
    """
    Run preflight validation on all credentials.

    Validates tokens and account access. Run this after
    updating credentials.json or if you encounter auth errors.
    """
    result = await run_preflight_checks(credential_manager)
    return format_preflight_result(result)
```

---

## Part 5: Server Startup Integration

### Modify `server.py`

```python
# Add to server.py startup

import asyncio
from .credentials import credential_manager
from .preflight import run_preflight_checks, format_preflight_result
import logging

logger = logging.getLogger(__name__)


async def startup_checks():
    """Run startup validation checks."""

    # Check for token expiration alerts
    alert = credential_manager.check_token_expiration_alerts()
    if alert:
        logger.warning(f"\n{alert}\n")

    # Run preflight validation
    logger.info("Running preflight validation...")
    result = await run_preflight_checks(credential_manager)

    if not result.passed:
        logger.error(f"\n{format_preflight_result(result)}\n")
        if result.errors:
            logger.error(
                "Preflight validation FAILED. Some accounts may not work. "
                "Run 'validate_credentials' tool to see details."
            )
    else:
        logger.info(
            f"Preflight validation passed. "
            f"{len(credential_manager.accounts)} accounts configured."
        )


# Call during server initialization
if __name__ == "__main__":
    asyncio.run(startup_checks())
    # ... rest of server startup
```

---

## Part 6: Implementation Workflow

Follow this process for **each phase** in the implementation:

### Step 1: Implement the Phase
Complete all code changes described in the phase checklist.

### Step 2: Audit & Fix Errors
Run the validation suite and fix any issues:

```bash
cd meta-ads-mcp
source venv/bin/activate

# Type checking (pyright-lsp)
pyright meta_ads_mcp/

# Run unit tests
python -m pytest tests/ -v

# Run specific tests for new modules
python -m pytest tests/test_credentials.py tests/test_rate_limiter.py -v
```

Use skills from `memory-bank/skills/` as needed:
- `test-runner` - For running and debugging tests
- `debug-mcp` - For troubleshooting server/auth issues
- `code-simplifier` - For code quality review

### Step 3: Update Progress
Document completion in `memory-bank/progress.md`:

```markdown
## Phase X: [Phase Name]
**Status:** Completed
**Date:** YYYY-MM-DD

### Completed
- [x] Task 1
- [x] Task 2

### Notes
- Any issues encountered and how they were resolved
- Decisions made during implementation
```

### Step 4: Request Approval
Ask user for confirmation before proceeding to the next phase:
- Summarize what was implemented
- Show test results
- Highlight any deviations from the plan
- Wait for explicit approval before starting next phase

### Plugins Used During Implementation

| Plugin | When to Use |
|--------|-------------|
| `pyright-lsp` | Type checking after each file change |
| `security-guidance` | Auto-monitors auth/credential code edits |
| `code-review` | Before completing each phase |
| `commit-commands` | `/commit` after each phase completion |

### Skills Used During Implementation

| Skill | When to Use |
|-------|-------------|
| `test-runner` | After implementing each module |
| `debug-mcp` | When encountering server/API issues |
| `code-simplifier` | Before finalizing code in each phase |
| `credential-setup` | When testing multi-credential configuration |

---

## Part 7: Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Create `credentials.py` with CredentialManager
- [ ] Create `rate_limiter.py` with per-key tracking
- [ ] Create `errors.py` with error classification
- [ ] Create `preflight.py` with validation checks

### Phase 2: Integration
- [ ] Modify `auth.py` to use credential_manager
- [ ] Modify `api.py` decorator for rate limiting
- [ ] Update all tool signatures with `account_name` parameter
- [ ] Add new MCP tools (list_accounts, switch_account, etc.)

### Phase 3: Server Integration
- [ ] Add startup preflight checks to server.py
- [ ] Add token expiration alerting
- [ ] Test with `.env` fallback (backward compatibility)

### Phase 4: Testing
- [ ] Unit tests for credential_manager
- [ ] Unit tests for rate_limiter
- [ ] Unit tests for error classification
- [ ] Integration test with 3 keys / 10 accounts config
- [ ] Test preflight validation with invalid tokens
- [ ] Test rate limit blocking behavior

### Phase 5: Documentation
- [ ] Update README with multi-account setup
- [ ] Document credentials.json format
- [ ] Add troubleshooting guide for common errors

---

## Part 8: Test Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| Valid 3 keys, 10 accounts | All preflight checks pass |
| One invalid token | That key fails, its accounts blocked, others work |
| One account inaccessible | That account fails preflight, others work |
| Rate limit exceeded on key | RateLimitError returned, retry_after provided |
| Token expires during use | TokenExpiredError, clear message |
| No credentials.json, valid .env | Falls back to single-account mode |
| No credentials at all | Clear error message at startup |
| switch_account to invalid name | Error with list of valid accounts |
| Call tool without account_name | Uses current account |
| Token expiring in < 7 days | Warning displayed at startup and in list_accounts |

---

## Part 9: Backward Compatibility

The system maintains full backward compatibility:

1. **No credentials.json**: Falls back to `.env` with single "default" account
2. **No account_name in tool calls**: Uses current account (or default)
3. **Existing tool signatures**: All parameters remain optional
4. **No behavior change**: Single-account users see no difference

---

## Appendix A: Quick Reference

### credentials.json Location
```
macOS:   ~/Library/Application Support/meta-ads-mcp/credentials.json
Windows: %APPDATA%\meta-ads-mcp\credentials.json
Linux:   ~/.config/meta-ads-mcp/credentials.json
```

### New MCP Tools
| Tool | Purpose |
|------|---------|
| `list_configured_accounts` | Show all accounts with status |
| `switch_account` | Change current account for session |
| `get_current_account` | Show active account details |
| `get_rate_limit_status` | Show rate limit status per key |
| `validate_credentials` | Run preflight validation manually |

### Rate Limit Tiers
| Tier | Max Score | Decay | Block Duration |
|------|-----------|-------|----------------|
| development | 60 | 5 min | 5 min |
| standard | 9,000 | 5 min | 1 min |

### Error Code Quick Reference
| Code | Meaning | Action |
|------|---------|--------|
| 4 | App rate limit | Retry after backoff |
| 17 | User rate limit | Retry after backoff |
| 190 | Invalid token | Don't retry, check credentials |
| 200 | Permission denied | Don't retry, check permissions |
| 613 | Calls limit | Retry after Retry-After header |
