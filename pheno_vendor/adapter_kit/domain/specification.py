"""Specification pattern for encapsulating query logic."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Abstract specification for filtering aggregates.

    The Specification pattern encapsulates business rules and query logic
    in a composable, reusable way. Specifications can be combined using
    logical operators.

    Example:
        >>> class ActiveUserSpec(Specification[User]):
        ...     def is_satisfied_by(self, user: User) -> bool:
        ...         return user.is_active
        >>>
        >>> class PremiumUserSpec(Specification[User]):
        ...     def is_satisfied_by(self, user: User) -> bool:
        ...         return user.subscription_tier == "premium"
        >>>
        >>> # Combine specifications
        >>> active_premium = ActiveUserSpec() & PremiumUserSpec()
        >>> users = repository.find(active_premium)
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies this specification.

        Args:
            candidate: The object to check

        Returns:
            True if candidate satisfies specification
        """
        ...

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Combine with AND logic.

        Args:
            other: Another specification

        Returns:
            Combined specification that requires both to be satisfied
        """
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Combine with OR logic.

        Args:
            other: Another specification

        Returns:
            Combined specification that requires either to be satisfied
        """
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Negate this specification.

        Returns:
            Specification that is satisfied when this one is not
        """
        return NotSpecification(self)

    def __and__(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Override & operator for AND logic."""
        return self.and_(other)

    def __or__(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Override | operator for OR logic."""
        return self.or_(other)

    def __invert__(self) -> "NotSpecification[T]":
        """Override ~ operator for NOT logic."""
        return self.not_()


class AndSpecification(Specification[T]):
    """Composite specification combining two specs with AND."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Both specifications must be satisfied."""
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """Composite specification combining two specs with OR."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """At least one specification must be satisfied."""
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    """Composite specification negating another spec."""

    def __init__(self, spec: Specification[T]):
        self.spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """Specification must NOT be satisfied."""
        return not self.spec.is_satisfied_by(candidate)
