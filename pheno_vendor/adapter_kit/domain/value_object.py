"""Base Value Object class for Domain-Driven Design.

Value Objects are immutable and defined by their attributes.
They have no identity and are interchangeable.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for all value objects.

    Value objects are immutable and have no identity. They are defined
    entirely by their attributes. Two value objects with the same
    attributes are considered equal.

    Key characteristics:
    - Immutable (frozen=True)
    - Equality based on attributes, not identity
    - No identity field
    - Side-effect free methods

    Example:
        >>> @dataclass(frozen=True)
        ... class Point(ValueObject):
        ...     x: float
        ...     y: float
        ...
        ...     def distance_from_origin(self) -> float:
        ...         return (self.x ** 2 + self.y ** 2) ** 0.5
        ...
        ...     def translate(self, dx: float, dy: float) -> 'Point':
        ...         return Point(self.x + dx, self.y + dy)
        >>>
        >>> p1 = Point(3.0, 4.0)
        >>> p2 = Point(3.0, 4.0)
        >>> p1 == p2  # True - same attributes
        >>> p1 is p2  # False - different objects
    """

    def validate(self) -> None:
        """Validate the value object's invariants.

        Override this method to implement validation logic.
        Should be called in __post_init__ if needed.

        Raises:
            ValueError: If validation fails
        """
        pass

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if all attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hash based on all attributes for use in sets and dicts."""
        return hash(tuple(sorted(self.__dict__.items())))
