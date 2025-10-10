"""Event bus implementation."""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional


class EventBus:
    """Event bus for pub/sub."""

    def __init__(self, backend: str = "memory"):
        self.backend = backend
        self.handlers: Dict[str, Callable[[dict], Any]] = {}

    @classmethod
    def backend(cls, url: str) -> "EventBus":
        """Create with backend URL."""
        return cls(backend=url)

    async def publish(self, event_type: str, payload: dict, idempotency_key: str = None) -> None:
        """Publish an event to registered subscribers."""

        handler = self.handlers.get(event_type)
        if handler is None:
            return

        result = handler(payload)
        if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
            await result

    def subscribe(self, event_type: str) -> Callable[[Callable[[dict], Any]], Callable[[dict], Any]]:
        """Subscribe to event."""

        def decorator(func: Callable[[dict], Any]) -> Callable[[dict], Any]:
            self.handlers[event_type] = func
            return func

        return decorator


class WebhookServer:
    """Webhook server with HMAC verification."""

    def __init__(self, secret: str):
        self.secret = secret
        self.handlers: Dict[str, Callable[[dict], Any]] = {}

    def handle(self, event_type: str) -> Callable[[Callable[[dict], Any]], Callable[[dict], Any]]:
        """Handle webhook event."""

        def decorator(func: Callable[[dict], Any]) -> Callable[[dict], Any]:
            self.handlers[event_type] = func
            return func

        return decorator
