"""In-memory realtime adapter for testing.

Provides realtime subscriptions and events using in-memory storage.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional

try:
    from ..adapters import RealtimeAdapter
except ImportError:
    from infrastructure.adapters import RealtimeAdapter


async def _maybe_await(x: Any):
    """Helper to await coroutines or return values directly."""
    if asyncio.iscoroutine(x):
        return await x
    return x


class InMemoryRealtimeAdapter(RealtimeAdapter):
    """In-memory realtime adapter for testing.
    
    Provides realtime subscriptions and events using in-memory storage.
    """
    
    def __init__(self):
        """Initialize in-memory realtime adapter."""
        self._subs: Dict[str, Dict[str, Any]] = {}
        self._next = 1

    async def subscribe(
        self,
        table: str,
        callback: Callable,
        *,
        filters: Optional[Dict[str, Any]] = None,
        events: Optional[List[str]] = None,
    ) -> str:
        """Subscribe to realtime events for a table."""
        sid = f"sub_{self._next}"
        self._next += 1
        self._subs[sid] = {
            "table": table,
            "callback": callback,
            "filters": filters or {},
            "events": set(events or ["INSERT", "UPDATE", "DELETE"]),
        }
        return sid

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from realtime events."""
        return bool(self._subs.pop(subscription_id, None))

    # helper to broadcast in tests
    async def _emit(self, table: str, event: str, row: Dict[str, Any]):
        """Emit a realtime event (helper for tests)."""
        for sub in self._subs.values():
            if sub["table"] == table and event in sub["events"]:
                await _maybe_await(sub["callback"]({"event": event, "row": row}))
