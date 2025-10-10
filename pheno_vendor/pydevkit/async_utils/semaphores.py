"""Async semaphores and rate limiters."""

import asyncio
import time
from typing import Optional


class RateLimitSemaphore:
    """
    Rate limiting semaphore.

    Example:
        limiter = RateLimitSemaphore(max_calls=10, time_window=60)
        
        async with limiter:
            await make_api_call()
    """

    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls = []
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._lock:
            now = time.time()
            # Remove old calls
            self._calls = [t for t in self._calls if now - t < self.time_window]
            
            # Wait if at limit
            while len(self._calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self._calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                now = time.time()
                self._calls = [t for t in self._calls if now - t < self.time_window]
            
            self._calls.append(now)

    async def __aexit__(self, *args):
        pass


class BoundedSemaphore:
    """
    Bounded semaphore for concurrency control.

    Example:
        sem = BoundedSemaphore(5)
        
        async with sem:
            await process_item()
    """

    def __init__(self, value: int):
        self._semaphore = asyncio.Semaphore(value)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *args):
        self._semaphore.release()
