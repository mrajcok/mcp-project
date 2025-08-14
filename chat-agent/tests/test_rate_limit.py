# ABOUT-ME: Tests for per-user rate limiting, global degraded state, and concurrency limits.
# ABOUT-ME: Uses an in-memory rate limiter to verify behavior without HTTP layer.

from datetime import datetime, timedelta, timezone

from src.rate_limiter import RateLimiter


def test_rate_limit_triggers_global_degraded():
    rl = RateLimiter(max_ops=50, window_secs=60, max_concurrent=3)
    user = "alice"

    now = datetime.now(timezone.utc)

    # 50 operations within the window are allowed
    for i in range(50):
        assert rl.record_operation(user, now=now) is True

    # 51st triggers degraded
    assert rl.record_operation(user, now=now) is False
    assert rl.global_degraded is True

    # When degraded, only login allowed
    assert rl.start_request(user, is_login=False) is False
    assert rl.start_request(user, is_login=True) is True
    rl.finish_request(user)


def test_concurrency_limit_per_user():
    rl = RateLimiter(max_ops=50, window_secs=60, max_concurrent=3)
    user = "bob"

    # Start up to 3 concurrent requests
    assert rl.start_request(user) is True
    assert rl.start_request(user) is True
    assert rl.start_request(user) is True

    # 4th should be rejected
    assert rl.start_request(user) is False

    # Finish one, then 4th should pass
    rl.finish_request(user)
    assert rl.start_request(user) is True


def test_window_slides_and_allows_after_time():
    rl = RateLimiter(max_ops=2, window_secs=60, max_concurrent=3)
    user = "carol"

    t0 = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert rl.record_operation(user, now=t0) is True
    assert rl.record_operation(user, now=t0) is True

    # Next op within window should trigger degraded when over limit
    assert rl.record_operation(user, now=t0) is False
    assert rl.global_degraded is True

    # Reset degraded for this test and move time beyond window
    rl.global_degraded = False
    t1 = t0 + timedelta(seconds=61)
    assert rl.record_operation(user, now=t1) is True
