"""Base Entity class for Domain-Driven Design.

Entities are objects that have a distinct identity that runs through time
and different representations. They are defined by a thread of continuity
and identity, not by their attributes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from .identity import Identity


T = TypeVar("T")


@dataclass
class Entity(Generic[T]):
    """Base class for all domain entities.

    An entity is defined by its identity, not its attributes.
    Two entities with the same ID are considered the same entity,
    even if their attributes differ.

    Attributes:
        id: Unique identifier for the entity
        created_at: Timestamp when entity was created
        updated_at: Timestamp when entity was last updated

    Example:
        >>> from domain_kit.entities import Entity, UUID4Identity
        >>>
        >>> @dataclass
        ... class User(Entity[UUID]):
        ...     username: str
        ...     email: str
        ...
        ...     def change_email(self, new_email: str):
        ...         self.email = new_email
        ...         self._mark_updated()
        >>>
        >>> user = User(
        ...     id=UUID4Identity.generate(),
        ...     username="john",
        ...     email="john@example.com"
        ... )
    """

    id: Identity[T]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same identity."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity for use in sets and dicts."""
        return hash(self.id)

    def _mark_updated(self) -> None:
        """Mark entity as updated (call after state changes)."""
        self.updated_at = datetime.now(timezone.utc)

    def is_same_as(self, other: "Entity") -> bool:
        """Check if this entity is the same as another."""
        return self == other

    def __repr__(self) -> str:
        """String representation showing entity type and ID."""
        return f"{self.__class__.__name__}(id={self.id})"


@dataclass
class AuditableEntity(Entity[T]):
    """Entity with full audit trail.

    Extends base Entity with created_by, updated_by tracking.

    Example:
        >>> @dataclass
        ... class Order(AuditableEntity[UUID]):
        ...     customer_id: UUID
        ...     total_amount: Money
    """

    created_by: str | None = None
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    is_deleted: bool = False

    def soft_delete(self, deleted_by: str) -> None:
        """Perform soft delete of entity."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by
        self._mark_updated()

    def restore(self) -> None:
        """Restore soft-deleted entity."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self._mark_updated()
