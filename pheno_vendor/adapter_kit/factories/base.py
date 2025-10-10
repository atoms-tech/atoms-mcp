"""Base factory pattern implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar, Generic

T = TypeVar('T')


class Factory(ABC, Generic[T]):
    """Abstract factory interface."""
    
    @abstractmethod
    def create(self, **kwargs) -> T:
        """Create an instance.
        
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            Created instance
        """
        pass


class Registry(Generic[T]):
    """Registry for factory pattern implementations."""
    
    def __init__(self):
        """Initialize registry."""
        self._implementations: Dict[str, Type[T]] = {}
    
    def register(self, name: str, implementation: Type[T]) -> "Registry[T]":
        """Register an implementation.
        
        Args:
            name: Name/key for the implementation
            implementation: Implementation class
            
        Returns:
            Self for chaining
        """
        self._implementations[name] = implementation
        return self
    
    def get(self, name: str) -> Type[T]:
        """Get implementation by name.
        
        Args:
            name: Name/key of implementation
            
        Returns:
            Implementation class
            
        Raises:
            KeyError: If name not registered
        """
        if name not in self._implementations:
            raise KeyError(f"No implementation registered for '{name}'")
        return self._implementations[name]
    
    def create(self, name: str, **kwargs) -> T:
        """Create instance by name.
        
        Args:
            name: Name/key of implementation
            **kwargs: Constructor arguments
            
        Returns:
            Created instance
        """
        impl_class = self.get(name)
        return impl_class(**kwargs)
    
    def list_implementations(self) -> list[str]:
        """List all registered implementations.
        
        Returns:
            List of registered names
        """
        return list(self._implementations.keys())
