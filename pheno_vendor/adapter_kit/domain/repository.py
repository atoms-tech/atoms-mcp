"""Repository interface for Domain-Driven Design.

Repositories mediate between the domain and data mapping layers using a
collection-like interface for accessing domain objects.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from ..entities import AggregateRoot, Identity


T = TypeVar("T", bound=AggregateRoot)
ID = TypeVar("ID")


class Repository(ABC, Generic[T, ID]):
    """Abstract base repository for synchronous operations.

    A repository represents a collection of aggregates. It encapsulates
    the logic required to access data sources and provides a more
    object-oriented view of the persistence layer.

    Example:
        >>> from domain_kit.repositories import Repository
        >>> from typing import Optional, List
        >>>
        >>> class OrderRepository(Repository[Order, UUID]):
        ...     def __init__(self, db_session):
        ...         self.db = db_session
        ...
        ...     def get(self, order_id: UUID) -> Optional[Order]:
        ...         # Implementation for database fetch
        ...         return self.db.query(Order).filter(Order.id == order_id).first()
        ...
        ...     def add(self, order: Order) -> None:
        ...         self.db.add(order)
        ...
        ...     def remove(self, order: Order) -> None:
        ...         self.db.delete(order)
    """

    @abstractmethod
    def get(self, entity_id: Identity[ID]) -> Optional[T]:
        """Retrieve an aggregate by ID.

        Args:
            entity_id: The identity of the aggregate to retrieve

        Returns:
            The aggregate if found, None otherwise
        """
        ...

    @abstractmethod
    def add(self, entity: T) -> None:
        """Add a new aggregate to the repository.

        Args:
            entity: The aggregate to add
        """
        ...

    @abstractmethod
    def update(self, entity: T) -> None:
        """Update an existing aggregate.

        Args:
            entity: The aggregate to update
        """
        ...

    @abstractmethod
    def remove(self, entity: T) -> None:
        """Remove an aggregate from the repository.

        Args:
            entity: The aggregate to remove
        """
        ...

    @abstractmethod
    def find(self, specification: "Specification[T]") -> List[T]:
        """Find aggregates matching a specification.

        Args:
            specification: The specification to match

        Returns:
            List of matching aggregates
        """
        ...

    def get_all(self) -> List[T]:
        """Get all aggregates in the repository.

        Returns:
            List of all aggregates
        """
        return self.find(specification=None)  # type: ignore


class AsyncRepository(ABC, Generic[T, ID]):
    """Abstract base repository for asynchronous operations.

    Same as Repository but with async/await support for
    async database operations.

    Example:
        >>> class AsyncOrderRepository(AsyncRepository[Order, UUID]):
        ...     def __init__(self, db_session):
        ...         self.db = db_session
        ...
        ...     async def get(self, order_id: UUID) -> Optional[Order]:
        ...         result = await self.db.execute(
        ...             select(Order).filter(Order.id == order_id)
        ...         )
        ...         return result.scalar_one_or_none()
        ...
        ...     async def add(self, order: Order) -> None:
        ...         self.db.add(order)
        ...         await self.db.flush()
    """

    @abstractmethod
    async def get(self, entity_id: Identity[ID]) -> Optional[T]:
        """Retrieve an aggregate by ID (async).

        Args:
            entity_id: The identity of the aggregate to retrieve

        Returns:
            The aggregate if found, None otherwise
        """
        ...

    @abstractmethod
    async def add(self, entity: T) -> None:
        """Add a new aggregate to the repository (async).

        Args:
            entity: The aggregate to add
        """
        ...

    @abstractmethod
    async def update(self, entity: T) -> None:
        """Update an existing aggregate (async).

        Args:
            entity: The aggregate to update
        """
        ...

    @abstractmethod
    async def remove(self, entity: T) -> None:
        """Remove an aggregate from the repository (async).

        Args:
            entity: The aggregate to remove
        """
        ...

    @abstractmethod
    async def find(self, specification: "Specification[T]") -> List[T]:
        """Find aggregates matching a specification (async).

        Args:
            specification: The specification to match

        Returns:
            List of matching aggregates
        """
        ...

    async def get_all(self) -> List[T]:
        """Get all aggregates in the repository (async).

        Returns:
            List of all aggregates
        """
        return await self.find(specification=None)  # type: ignore


# Import specification after to avoid circular imports
from .specification import Specification  # noqa: E402

# Update forward references
Repository.find.__annotations__["specification"] = Specification[T]
AsyncRepository.find.__annotations__["specification"] = Specification[T]
