"""Rate limiter for external API calls."""

from __future__ import annotations

import asyncio
import time
from collections import deque


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.monotonic()

            # Remove expired timestamps
            while self._timestamps and now - self._timestamps[0] > self.window:
                self._timestamps.popleft()

            # Wait if at capacity
            if len(self._timestamps) >= self.max_requests:
                wait_time = self._timestamps[0] + self.window - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up after waiting
                    now = time.monotonic()
                    while self._timestamps and now - self._timestamps[0] > self.window:
                        self._timestamps.popleft()

            self._timestamps.append(time.monotonic())

    @property
    def available(self) -> int:
        """Number of available request slots."""
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] > self.window:
            self._timestamps.popleft()
        return max(0, self.max_requests - len(self._timestamps))
