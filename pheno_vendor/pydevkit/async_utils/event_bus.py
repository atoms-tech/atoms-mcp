"""Event bus for async event handling."""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    """Event data."""
    name: str
    data: Any


class EventBus:
    """
    Async event bus.

    Example:
        bus = EventBus()
        
        @bus.on("user_login")
        async def handle_login(event):
            print(f"User logged in: {event.data}")
        
        await bus.emit("user_login", {"user_id": 123})
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def on(self, event_name: str):
        """Register event handler decorator."""
        def decorator(handler: Callable):
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
            return handler
        return decorator

    def off(self, event_name: str, handler: Callable = None):
        """Remove event handler."""
        if event_name not in self._handlers:
            return

        if handler is None:
            del self._handlers[event_name]
        else:
            self._handlers[event_name].remove(handler)

    async def emit(self, event_name: str, data: Any = None):
        """Emit event to all handlers."""
        if event_name not in self._handlers:
            return

        event = Event(event_name, data)
        tasks = [handler(event) for handler in self._handlers[event_name]]
        await asyncio.gather(*tasks, return_exceptions=True)
