"""Dependency injection container for clean architecture."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar('T')


class Container:
    """Simple dependency injection container."""
    
    def __init__(self):
        """Initialize container."""
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._instances: Dict[Type, Any] = {}
    
    def register(
        self,
        interface: Type[T],
        implementation: Type[T] | Callable[..., T],
        singleton: bool = False
    ) -> "Container":
        """Register a dependency.
        
        Args:
            interface: Interface/abstract class
            implementation: Concrete implementation or factory function
            singleton: If True, create only one instance
            
        Returns:
            Self for chaining
        """
        if singleton:
            self._singletons[interface] = implementation
        else:
            self._factories[interface] = implementation
        
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> "Container":
        """Register an existing instance.
        
        Args:
            interface: Interface/abstract class
            instance: Instance to register
            
        Returns:
            Self for chaining
        """
        self._instances[interface] = instance
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency.
        
        Args:
            interface: Interface to resolve
            
        Returns:
            Instance of the interface
            
        Raises:
            KeyError: If interface not registered
        """
        # Check instances first
        if interface in self._instances:
            return self._instances[interface]
        
        # Check singletons
        if interface in self._singletons:
            factory = self._singletons[interface]
            if interface not in self._instances:
                # Create singleton instance
                if callable(factory):
                    self._instances[interface] = factory()
                else:
                    self._instances[interface] = factory
            return self._instances[interface]
        
        # Check factories
        if interface in self._factories:
            factory = self._factories[interface]
            if callable(factory):
                return factory()
            return factory()
        
        raise KeyError(f"No registration found for {interface}")
    
    def clear(self):
        """Clear all registrations."""
        self._factories.clear()
        self._singletons.clear()
        self._instances.clear()


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get global container instance.
    
    Returns:
        Global container
    """
    return _container


def inject(interface: Type[T]) -> T:
    """Inject dependency from global container.
    
    Args:
        interface: Interface to inject
        
    Returns:
        Instance of the interface
    """
    return _container.resolve(interface)
