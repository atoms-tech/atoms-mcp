"""Repository pattern for data access abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar('T')
ID = TypeVar('ID')


class Repository(ABC, Generic[T, ID]):
    """Abstract repository interface."""
    
    @abstractmethod
    async def get_by_id(self, id: ID) -> Optional[T]:
        """Get entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            Entity or None if not found
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """List entities with optional filtering.
        
        Args:
            filters: Filter conditions
            limit: Maximum number of results
            offset: Result offset for pagination
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update).
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with updated fields
        """
        pass
    
    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Delete entity by ID.
        
        Args:
            id: Entity identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching filters.
        
        Args:
            filters: Filter conditions
            
        Returns:
            Count of matching entities
        """
        pass


class InMemoryRepository(Repository[T, ID]):
    """In-memory repository implementation for testing."""
    
    def __init__(self):
        """Initialize in-memory repository."""
        self._storage: Dict[ID, T] = {}
        self._next_id: int = 1
    
    async def get_by_id(self, id: ID) -> Optional[T]:
        """Get entity by ID."""
        return self._storage.get(id)
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """List entities."""
        entities = list(self._storage.values())
        
        # Apply filters (simple equality check)
        if filters:
            filtered = []
            for entity in entities:
                match = True
                for key, value in filters.items():
                    if not hasattr(entity, key) or getattr(entity, key) != value:
                        match = False
                        break
                if match:
                    filtered.append(entity)
            entities = filtered
        
        # Apply pagination
        if offset:
            entities = entities[offset:]
        if limit:
            entities = entities[:limit]
        
        return entities
    
    async def save(self, entity: T) -> T:
        """Save entity."""
        # Simple ID assignment if entity has 'id' attribute
        if hasattr(entity, 'id'):
            entity_id = getattr(entity, 'id')
            if entity_id is None:
                setattr(entity, 'id', self._next_id)
                self._next_id += 1
            self._storage[getattr(entity, 'id')] = entity
        return entity
    
    async def delete(self, id: ID) -> bool:
        """Delete entity."""
        if id in self._storage:
            del self._storage[id]
            return True
        return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities."""
        entities = await self.list(filters=filters)
        return len(entities)
