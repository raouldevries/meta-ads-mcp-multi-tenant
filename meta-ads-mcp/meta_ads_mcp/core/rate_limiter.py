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
    _lock_class = threading.Lock()

    def __new__(cls):
        with cls._lock_class:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._states: Dict[str, KeyRateLimitState] = {}
        self._lock = threading.RLock()  # RLock allows re-entrant locking
        self._initialized = True

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        with cls._lock_class:
            cls._instance = None

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


# Singleton instance - lazy initialization
def get_rate_limiter() -> RateLimiter:
    """Get the singleton RateLimiter instance."""
    return RateLimiter()
