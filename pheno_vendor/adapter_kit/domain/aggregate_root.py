"""Aggregate Root pattern for Domain-Driven Design.

An Aggregate is a cluster of associated objects that are treated as a unit
for data changes. The Aggregate Root is the parent entity through which
all interactions with the aggregate occur.
"""

from dataclasses import dataclass, field
from typing import Generic, List, TypeVar

from .entity import Entity
from ..events import DomainEvent


T = TypeVar("T")


@dataclass
class AggregateRoot(Entity[T], Generic[T]):
    """Base class for aggregate roots.

    An aggregate root is the entry point to an aggregate - a cluster of
    domain objects that can be treated as a single unit. Only the aggregate
    root can be obtained directly via queries; everything else must be
    reached through traversal.

    Key responsibilities:
    - Enforce invariants across the aggregate
    - Manage domain events
    - Control access to aggregate members

    Example:
        >>> from dataclasses import dataclass
        >>> from domain_kit.entities import AggregateRoot, UUID4Identity
        >>> from domain_kit.events import DomainEvent
        >>>
        >>> @dataclass
        ... class OrderPlaced(DomainEvent):
        ...     order_id: str
        ...     customer_id: str
        ...     total: float
        >>>
        >>> @dataclass
        ... class Order(AggregateRoot[UUID]):
        ...     customer_id: str
        ...     items: List[OrderItem] = field(default_factory=list)
        ...     status: str = "pending"
        ...
        ...     def place_order(self):
        ...         # Business logic
        ...         self.status = "placed"
        ...         # Raise domain event
        ...         self.raise_event(OrderPlaced(
        ...             order_id=str(self.id),
        ...             customer_id=self.customer_id,
        ...             total=self.total_amount()
        ...         ))
        ...
        ...     def add_item(self, item: OrderItem):
        ...         self.items.append(item)
        ...         self._mark_updated()
        ...
        ...     def total_amount(self) -> float:
        ...         return sum(item.price * item.quantity for item in self.items)
    """

    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    _version: int = field(default=1, init=False)

    def raise_event(self, event: DomainEvent) -> None:
        """Raise a domain event.

        Domain events represent something that happened in the domain that
        domain experts care about. They are collected and published after
        the aggregate is successfully persisted.

        Args:
            event: The domain event to raise
        """
        self._domain_events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events raised by this aggregate.

        Returns:
            List of domain events that haven't been published yet
        """
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear all domain events.

        Should be called after events have been successfully published.
        """
        self._domain_events.clear()

    def increment_version(self) -> None:
        """Increment the version number for optimistic concurrency control."""
        self._version += 1
        self._mark_updated()

    @property
    def version(self) -> int:
        """Get the current version number."""
        return self._version

    def validate_invariants(self) -> None:
        """Validate all business invariants for this aggregate.

        Override this method to implement aggregate-specific validation rules.
        Should be called before persisting the aggregate.

        Raises:
            ValueError: If any invariant is violated
        """
        pass  # Override in subclasses


@dataclass
class AggregateNotFoundException(Exception):
    """Raised when an aggregate cannot be found."""

    aggregate_type: str
    aggregate_id: str

    def __str__(self) -> str:
        return f"{self.aggregate_type} with ID {self.aggregate_id} not found"


@dataclass
class ConcurrencyException(Exception):
    """Raised when a concurrency conflict is detected."""

    aggregate_type: str
    aggregate_id: str
    expected_version: int
    actual_version: int

    def __str__(self) -> str:
        return (
            f"Concurrency conflict for {self.aggregate_type} {self.aggregate_id}: "
            f"expected version {self.expected_version}, found {self.actual_version}"
        )
