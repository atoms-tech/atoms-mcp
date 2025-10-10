"""Event Publisher for publishing domain events."""

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Type

from .domain_event import DomainEvent


class EventPublisher(ABC):
    """Abstract event publisher for domain events.

    Publishers are responsible for dispatching events to registered handlers.
    """

    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers.

        Args:
            event: The domain event to publish
        """
        ...

    @abstractmethod
    def subscribe(
        self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when event occurs
        """
        ...


class InMemoryEventPublisher(EventPublisher):
    """Simple in-memory event publisher for testing and simple scenarios.

    Example:
        >>> from domain_kit.events import InMemoryEventPublisher, DomainEvent
        >>> from dataclasses import dataclass
        >>>
        >>> @dataclass(frozen=True)
        ... class UserRegistered(DomainEvent):
        ...     user_id: str
        ...     email: str
        >>>
        >>> publisher = InMemoryEventPublisher()
        >>>
        >>> def send_welcome_email(event: UserRegistered):
        ...     print(f"Sending welcome email to {event.email}")
        >>>
        >>> publisher.subscribe(UserRegistered, send_welcome_email)
        >>> event = UserRegistered(user_id="123", email="user@example.com")
        >>> publisher.publish(event)
        Sending welcome email to user@example.com
    """

    def __init__(self):
        self._handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    def publish(self, event: DomainEvent) -> None:
        """Publish event to all subscribed handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler for {event_type.__name__}: {e}")

    def subscribe(
        self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe handler to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def clear_handlers(self, event_type: Type[DomainEvent] = None) -> None:  # type: ignore
        """Clear all handlers for a specific event type or all handlers.

        Args:
            event_type: Event type to clear handlers for. If None, clears all.
        """
        if event_type is None:
            self._handlers.clear()
        elif event_type in self._handlers:
            del self._handlers[event_type]


class AsyncEventPublisher(ABC):
    """Abstract async event publisher for domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers (async).

        Args:
            event: The domain event to publish
        """
        ...

    @abstractmethod
    def subscribe(
        self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of event to subscribe to
            handler: The async handler function to call when event occurs
        """
        ...


# Global singleton publisher (can be replaced with DI in production)
_global_publisher = InMemoryEventPublisher()


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    return _global_publisher


def set_event_publisher(publisher: EventPublisher) -> None:
    """Set the global event publisher instance."""
    global _global_publisher
    _global_publisher = publisher
