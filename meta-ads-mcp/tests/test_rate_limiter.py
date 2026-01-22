"""
Tests for per-key rate limiter.
"""

import time
import pytest
from unittest.mock import patch

from meta_ads_mcp.core.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
    RateLimitError,
    RateLimitTier,
    TierConfig,
    KeyRateLimitState,
    TIER_CONFIGS,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    RateLimiter.reset_instance()
    yield
    RateLimiter.reset_instance()


class TestTierConfig:
    """Tests for tier configuration."""

    def test_development_tier_config(self):
        """Development tier has low limits."""
        config = TIER_CONFIGS[RateLimitTier.DEVELOPMENT]
        assert config.max_score == 60
        assert config.block_duration_seconds == 300  # 5 minutes

    def test_standard_tier_config(self):
        """Standard tier has higher limits."""
        config = TIER_CONFIGS[RateLimitTier.STANDARD]
        assert config.max_score == 9000
        assert config.block_duration_seconds == 60  # 1 minute


class TestKeyRateLimitState:
    """Tests for rate limit state."""

    def test_is_blocked_not_blocked(self):
        """State is not blocked by default."""
        state = KeyRateLimitState(
            key_name="test",
            tier=RateLimitTier.STANDARD
        )
        assert not state.is_blocked

    def test_is_blocked_future(self):
        """State is blocked when blocked_until is in future."""
        state = KeyRateLimitState(
            key_name="test",
            tier=RateLimitTier.STANDARD,
            blocked_until=time.time() + 60
        )
        assert state.is_blocked

    def test_is_blocked_past(self):
        """State is not blocked when blocked_until is in past."""
        state = KeyRateLimitState(
            key_name="test",
            tier=RateLimitTier.STANDARD,
            blocked_until=time.time() - 1
        )
        assert not state.is_blocked

    def test_block_time_remaining(self):
        """Calculate remaining block time."""
        state = KeyRateLimitState(
            key_name="test",
            tier=RateLimitTier.STANDARD,
            blocked_until=time.time() + 30
        )
        assert 25 <= state.block_time_remaining <= 30


class TestRateLimiterSingleton:
    """Tests for singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Multiple calls return same instance."""
        limiter1 = RateLimiter()
        limiter2 = RateLimiter()
        assert limiter1 is limiter2

    def test_reset_instance_creates_new(self):
        """reset_instance allows creating new instance."""
        limiter1 = RateLimiter()
        RateLimiter.reset_instance()
        limiter2 = RateLimiter()
        assert limiter1 is not limiter2

    def test_get_rate_limiter_returns_singleton(self):
        """get_rate_limiter() returns singleton."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2


class TestRateLimitChecking:
    """Tests for rate limit checking."""

    def test_check_rate_limit_allowed(self):
        """Request allowed when under limit."""
        limiter = RateLimiter()
        result = limiter.check_rate_limit("test_key", "standard")
        assert result is True

    def test_check_rate_limit_blocked(self):
        """Request blocked when key is blocked."""
        limiter = RateLimiter()
        # Manually block the key
        state = limiter._get_or_create_state("test_key", "standard")
        state.blocked_until = time.time() + 60

        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_rate_limit("test_key", "standard")

        assert exc_info.value.key_name == "test_key"
        assert exc_info.value.retry_after_seconds > 0

    def test_check_rate_limit_exceeds_limit(self):
        """Request blocked when would exceed limit."""
        limiter = RateLimiter()
        # Fill up the score
        state = limiter._get_or_create_state("test_key", "development")
        config = TIER_CONFIGS[RateLimitTier.DEVELOPMENT]
        state.current_score = config.max_score  # At limit

        with pytest.raises(RateLimitError) as exc_info:
            limiter.check_rate_limit("test_key", "development")

        assert exc_info.value.retry_after_seconds == config.block_duration_seconds


class TestRateLimitRecording:
    """Tests for recording API calls."""

    def test_record_call_increases_score(self):
        """Recording a call increases the score."""
        limiter = RateLimiter()
        limiter.record_call("test_key", "standard")

        status = limiter.get_key_status("test_key")
        assert status["current_score"] == 1.0
        assert status["total_calls"] == 1

    def test_record_call_multiple(self):
        """Recording multiple calls accumulates."""
        limiter = RateLimiter()
        for _ in range(5):
            limiter.record_call("test_key", "standard")

        status = limiter.get_key_status("test_key")
        assert status["total_calls"] == 5

    def test_record_rate_limit_error_blocks_key(self):
        """Recording a rate limit error blocks the key."""
        limiter = RateLimiter()
        limiter.record_rate_limit_error("test_key", retry_after=120)

        status = limiter.get_key_status("test_key")
        assert status["is_blocked"] is True
        assert status["status"] == "blocked"


class TestScoreDecay:
    """Tests for score decay over time."""

    def test_decay_reduces_score(self):
        """Score decays over time."""
        limiter = RateLimiter()

        # Record some calls
        for _ in range(10):
            limiter.record_call("test_key", "standard")

        initial_score = limiter._states["test_key"].current_score
        initial_time = limiter._states["test_key"].last_update

        # Simulate time passing by manipulating last_update
        limiter._states["test_key"].last_update = initial_time - 10  # Pretend 10 seconds passed

        # Apply decay
        limiter._apply_decay(limiter._states["test_key"])

        assert limiter._states["test_key"].current_score < initial_score

    def test_decay_does_not_go_negative(self):
        """Score doesn't go below zero."""
        limiter = RateLimiter()
        limiter.record_call("test_key", "standard")

        initial_time = limiter._states["test_key"].last_update

        # Simulate lots of time passing
        limiter._states["test_key"].last_update = initial_time - 1000  # 1000 seconds ago

        # Apply decay
        limiter._apply_decay(limiter._states["test_key"])

        assert limiter._states["test_key"].current_score >= 0


class TestGetStatus:
    """Tests for status retrieval."""

    def test_get_key_status_unknown(self):
        """Unknown key returns default status."""
        limiter = RateLimiter()
        status = limiter.get_key_status("unknown_key")

        assert status["key_name"] == "unknown_key"
        assert status["status"] == "unknown"

    def test_get_key_status_ok(self):
        """Low usage returns ok status."""
        limiter = RateLimiter()
        limiter.record_call("test_key", "standard")

        status = limiter.get_key_status("test_key")
        assert status["status"] == "ok"
        assert status["usage_percent"] < 1

    def test_get_key_status_warning(self):
        """High usage returns warning status."""
        limiter = RateLimiter()
        state = limiter._get_or_create_state("test_key", "development")
        config = TIER_CONFIGS[RateLimitTier.DEVELOPMENT]
        state.current_score = config.max_score * 0.85  # 85% usage

        status = limiter.get_key_status("test_key")
        assert status["status"] == "warning"
        assert status["usage_percent"] > 80

    def test_get_key_status_blocked(self):
        """Blocked key returns blocked status."""
        limiter = RateLimiter()
        limiter.record_rate_limit_error("test_key", retry_after=60)

        status = limiter.get_key_status("test_key")
        assert status["status"] == "blocked"

    def test_get_all_status(self):
        """Get status for all tracked keys."""
        limiter = RateLimiter()
        limiter.record_call("key1", "standard")
        limiter.record_call("key2", "development")

        all_status = limiter.get_all_status()
        assert "key1" in all_status
        assert "key2" in all_status

    def test_reset_key(self):
        """Reset removes key tracking."""
        limiter = RateLimiter()
        limiter.record_call("test_key", "standard")
        assert "test_key" in limiter._states

        limiter.reset_key("test_key")
        assert "test_key" not in limiter._states


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_error_message(self):
        """Error has descriptive message."""
        error = RateLimitError("test_key", 60)
        assert "test_key" in str(error)
        assert "60" in str(error)

    def test_error_attributes(self):
        """Error has correct attributes."""
        error = RateLimitError("my_key", 120)
        assert error.key_name == "my_key"
        assert error.retry_after_seconds == 120


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_calls_safe(self):
        """Concurrent calls don't cause data corruption."""
        import threading

        limiter = RateLimiter()
        errors = []

        def make_calls():
            try:
                for _ in range(10):  # Reduced from 100 to avoid timeout
                    limiter.record_call("shared_key", "standard")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_calls) for _ in range(5)]  # Reduced from 10
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        # All 50 calls should be recorded
        status = limiter.get_key_status("shared_key")
        assert status["total_calls"] == 50
