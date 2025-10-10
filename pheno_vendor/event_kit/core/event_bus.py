"""Event bus for publish-subscribe messaging."""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


@dataclass
class Event:
    """Event data structure."""
    name: str
    data: Any
    timestamp: datetime = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventBus:
    """
    In-memory event bus with pub/sub pattern.
    
    Features:
    - Async event handlers
    - Wildcard subscriptions
    - Event filtering
    - Error handling
    
    Example:
        bus = EventBus()
        
        @bus.on("user.created")
        async def send_welcome_email(event):
            await email.send(event.data["email"])
        
        await bus.publish("user.created", {"email": "user@example.com"})
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._wildcard_handlers: List[Callable] = []
    
    def on(self, event_name: str):
        """
        Decorator to register event handler.
        
        Args:
            event_name: Event name or wildcard pattern (e.g., "user.*")
        """
        def decorator(handler: Callable):
            if "*" in event_name:
                self._wildcard_handlers.append((event_name, handler))
            else:
                if event_name not in self._handlers:
                    self._handlers[event_name] = []
                self._handlers[event_name].append(handler)
            return handler
        return decorator
    
    def subscribe(self, event_name: str, handler: Callable):
        """
        Subscribe to events.
        
        Args:
            event_name: Event name or wildcard
            handler: Async handler function
        """
        if "*" in event_name:
            self._wildcard_handlers.append((event_name, handler))
        else:
            if event_name not in self._handlers:
                self._handlers[event_name] = []
            self._handlers[event_name].append(handler)
    
    def unsubscribe(self, event_name: str, handler: Optional[Callable] = None):
        """
        Unsubscribe from events.
        
        Args:
            event_name: Event name
            handler: Specific handler to remove (None = remove all)
        """
        if handler is None:
            self._handlers.pop(event_name, None)
        elif event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name] if h != handler
            ]
    
    async def publish(
        self,
        event_name: str,
        data: Any = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Event:
        """
        Publish event to all subscribers.
        
        Args:
            event_name: Event name
            data: Event data
            source: Event source identifier
            correlation_id: Correlation ID for tracing
            
        Returns:
            Published event
        """
        event = Event(
            name=event_name,
            data=data,
            source=source,
            correlation_id=correlation_id,
        )
        
        # Get handlers
        handlers = self._handlers.get(event_name, []).copy()
        
        # Add wildcard handlers
        for pattern, handler in self._wildcard_handlers:
            if self._matches_pattern(event_name, pattern):
                handlers.append(handler)
        
        # Execute handlers concurrently
        if handlers:
            tasks = [self._call_handler(handler, event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return event
    
    async def _call_handler(self, handler: Callable, event: Event):
        """Call handler with error handling."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            # Log error but don't stop other handlers
            print(f"Error in event handler: {e}")
    
    def _matches_pattern(self, event_name: str, pattern: str) -> bool:
        """Check if event name matches wildcard pattern."""
        if pattern == "*":
            return True
        
        pattern_parts = pattern.split(".")
        name_parts = event_name.split(".")
        
        if len(pattern_parts) != len(name_parts):
            return False
        
        for p, n in zip(pattern_parts, name_parts):
            if p != "*" and p != n:
                return False
        
        return True
    
    def clear(self):
        """Clear all handlers."""
        self._handlers.clear()
        self._wildcard_handlers.clear()
    
    def get_handlers(self, event_name: str) -> List[Callable]:
        """Get handlers for event name."""
        return self._handlers.get(event_name, []).copy()
