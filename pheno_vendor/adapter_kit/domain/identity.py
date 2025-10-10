"""Identity value objects for domain entities.

Identity is the defining characteristic of an entity.
These are immutable value objects that represent unique identifiers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4


T = TypeVar("T")


@dataclass(frozen=True)
class Identity(ABC, Generic[T]):
    """Abstract base for entity identities.

    All identities are immutable value objects that uniquely identify entities.
    """

    value: T

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the identity."""
        ...

    def __eq__(self, other: Any) -> bool:
        """Identity equality based on value."""
        if not isinstance(other, Identity):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        """Hash based on value for use in sets and dicts."""
        return hash(self.value)


@dataclass(frozen=True)
class UUID4Identity(Identity[UUID]):
    """UUID-based identity for entities.

    Example:
        >>> user_id = UUID4Identity.generate()
        >>> str(user_id)
        'a1b2c3d4-...'
    """

    @classmethod
    def generate(cls) -> "UUID4Identity":
        """Generate a new random UUID identity."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "UUID4Identity":
        """Create identity from UUID string."""
        return cls(value=UUID(id_string))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class StringIdentity(Identity[str]):
    """String-based identity for entities.

    Useful for human-readable identifiers like slugs, codes, etc.

    Example:
        >>> product_id = StringIdentity("PROD-12345")
        >>> str(product_id)
        'PROD-12345'
    """

    def __str__(self) -> str:
        return self.value

    def validate_pattern(self, pattern: str) -> bool:
        """Validate identity against regex pattern."""
        import re
        return bool(re.match(pattern, self.value))


@dataclass(frozen=True)
class IntegerIdentity(Identity[int]):
    """Integer-based identity for entities.

    Useful for auto-incrementing database IDs.

    Example:
        >>> order_id = IntegerIdentity(12345)
        >>> str(order_id)
        '12345'
    """

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value
