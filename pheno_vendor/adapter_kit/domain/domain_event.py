"""Domain Event base class."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Domain events represent something that happened in the past.
    They are immutable and should be named in past tense.

    Attributes:
        event_id: Unique identifier for this event
        occurred_at: When the event occurred
        event_version: Version of the event schema (for evolution)

    Example:
        >>> from dataclasses import dataclass
        >>> from domain_kit.events import DomainEvent
        >>>
        >>> @dataclass(frozen=True)
        ... class OrderPlaced(DomainEvent):
        ...     order_id: str
        ...     customer_id: str
        ...     total_amount: float
        ...     items: tuple  # Must be immutable
        >>>
        >>> event = OrderPlaced(
        ...     order_id="ORD-123",
        ...     customer_id="CUST-456",
        ...     total_amount=99.99,
        ...     items=("item1", "item2")
        ... )
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.__class__.__name__,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "payload": {
                k: v
                for k, v in self.__dict__.items()
                if k not in ("event_id", "occurred_at", "event_version")
            },
        }

    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__
