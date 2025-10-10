"""Unit of Work pattern for transaction management."""

from abc import ABC, abstractmethod
from typing import Any


class UnitOfWork(ABC):
    """Abstract Unit of Work for managing transactions.

    The Unit of Work pattern maintains a list of objects affected by a
    business transaction and coordinates the writing out of changes.

    Example:
        >>> class SQLAlchemyUnitOfWork(UnitOfWork):
        ...     def __init__(self, session_factory):
        ...         self.session_factory = session_factory
        ...
        ...     def __enter__(self):
        ...         self.session = self.session_factory()
        ...         return self
        ...
        ...     def __exit__(self, *args):
        ...         self.rollback()
        ...         self.session.close()
        ...
        ...     def commit(self):
        ...         self.session.commit()
        ...
        ...     def rollback(self):
        ...         self.session.rollback()
        >>>
        >>> with uow:
        ...     order = Order(...)
        ...     uow.orders.add(order)
        ...     uow.commit()
    """

    @abstractmethod
    def commit(self) -> None:
        """Commit all changes in this unit of work."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Rollback all changes in this unit of work."""
        ...

    def __enter__(self) -> "UnitOfWork":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager, rollback on exception."""
        if exc_type is not None:
            self.rollback()


class AsyncUnitOfWork(ABC):
    """Abstract Unit of Work for async transaction management.

    Async version of UnitOfWork for async database operations.

    Example:
        >>> class AsyncSQLAlchemyUnitOfWork(AsyncUnitOfWork):
        ...     def __init__(self, session_factory):
        ...         self.session_factory = session_factory
        ...
        ...     async def __aenter__(self):
        ...         self.session = self.session_factory()
        ...         return self
        ...
        ...     async def __aexit__(self, *args):
        ...         await self.rollback()
        ...         await self.session.close()
        ...
        ...     async def commit(self):
        ...         await self.session.commit()
        ...
        ...     async def rollback(self):
        ...         await self.session.rollback()
        >>>
        >>> async with uow:
        ...     order = Order(...)
        ...     await uow.orders.add(order)
        ...     await uow.commit()
    """

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes in this unit of work (async)."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes in this unit of work (async)."""
        ...

    async def __aenter__(self) -> "AsyncUnitOfWork":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager, rollback on exception."""
        if exc_type is not None:
            await self.rollback()
