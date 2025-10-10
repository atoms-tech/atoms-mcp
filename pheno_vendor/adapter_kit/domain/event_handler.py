"""Event handler decorators and base classes."""

from abc import ABC, abstractmethod
from typing import Callable, Type, TypeVar

from .domain_event import DomainEvent
from .event_publisher import get_event_publisher


T = TypeVar("T", bound=DomainEvent)


class EventHandler(ABC):
    """Abstract base class for event handlers.

    Example:
        >>> class SendWelcomeEmailHandler(EventHandler):
        ...     def handle(self, event: UserRegistered) -> None:
        ...         email_service.send_welcome_email(event.email)
        ...
        ...     def event_type(self) -> Type[DomainEvent]:
        ...         return UserRegistered
    """

    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle the domain event.

        Args:
            event: The domain event to handle
        """
        ...

    @abstractmethod
    def event_type(self) -> Type[DomainEvent]:
        """Get the event type this handler processes.

        Returns:
            The event class this handler handles
        """
        ...


def event_handler(event_type: Type[T]) -> Callable[[Callable[[T], None]], Callable[[T], None]]:
    """Decorator for registering event handlers.

    Automatically registers the decorated function as a handler for
    the specified event type with the global event publisher.

    Args:
        event_type: The type of event this handler processes

    Example:
        >>> from domain_kit.events import event_handler, DomainEvent
        >>> from dataclasses import dataclass
        >>>
        >>> @dataclass(frozen=True)
        ... class OrderShipped(DomainEvent):
        ...     order_id: str
        ...     tracking_number: str
        >>>
        >>> @event_handler(OrderShipped)
        ... def send_shipping_notification(event: OrderShipped):
        ...     print(f"Order {event.order_id} shipped: {event.tracking_number}")
        >>>
        >>> # Handler is automatically registered
        >>> event = OrderShipped(order_id="123", tracking_number="TRACK-456")
        >>> get_event_publisher().publish(event)
        Order 123 shipped: TRACK-456
    """

    def decorator(func: Callable[[T], None]) -> Callable[[T], None]:
        # Register handler with global publisher
        publisher = get_event_publisher()
        publisher.subscribe(event_type, func)  # type: ignore
        return func

    return decorator


def async_event_handler(
    event_type: Type[T],
) -> Callable[[Callable[[T], None]], Callable[[T], None]]:
    """Decorator for registering async event handlers.

    Similar to event_handler but for async functions.

    Args:
        event_type: The type of event this handler processes

    Example:
        >>> @async_event_handler(OrderShipped)
        ... async def send_shipping_notification(event: OrderShipped):
        ...     await email_service.send_notification(event.order_id)
    """

    def decorator(func: Callable[[T], None]) -> Callable[[T], None]:
        # Register handler with global publisher
        publisher = get_event_publisher()
        publisher.subscribe(event_type, func)  # type: ignore
        return func

    return decorator
