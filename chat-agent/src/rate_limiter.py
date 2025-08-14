# ABOUT-ME: In-memory rate limiter with global degraded state and per-user concurrency limits.
# ABOUT-ME: Provides RateLimiter class to track ops per 60s window and enforce max concurrent requests.

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict


@dataclass
class _UserState:
    ops: Deque[datetime]
    concurrent: int = 0


class RateLimiter:
    def __init__(self, max_ops: int = 50, window_secs: int = 60, max_concurrent: int = 3) -> None:
        self.max_ops = max_ops
        self.window = timedelta(seconds=window_secs)
        self.max_concurrent = max_concurrent
        self.global_degraded: bool = False
        self._state: Dict[str, _UserState] = defaultdict(lambda: _UserState(ops=deque()))

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _prune(self, user: str, now: datetime) -> None:
        ops = self._state[user].ops
        cutoff = now - self.window
        while ops and ops[0] <= cutoff:
            ops.popleft()

    def record_operation(self, user: str, *, now: datetime | None = None) -> bool:
        """
        Record an operation for a user. Returns True if under limit; if this pushes the
        user over the limit, sets global_degraded=True and returns False.
        """
        if self.global_degraded:
            return False
        now = now or self._now()
        st = self._state[user]
        self._prune(user, now)
        st.ops.append(now)
        if len(st.ops) > self.max_ops:
            self.global_degraded = True
            return False
        return True

    def start_request(self, user: str, *, is_login: bool = False) -> bool:
        if self.global_degraded and not is_login:
            return False
        st = self._state[user]
        if st.concurrent >= self.max_concurrent:
            return False
        st.concurrent += 1
        return True

    def finish_request(self, user: str) -> None:
        st = self._state[user]
        if st.concurrent > 0:
            st.concurrent -= 1
