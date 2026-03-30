"""Token bucket rate limiter for API calls."""

import asyncio
import time


class RateLimiter:
    """
    Simple token bucket rate limiter.
    Ensures we don't exceed requests_per_minute.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self._min_interval = 60.0 / requests_per_minute
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until we're allowed to make the next request."""
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
