"""Base index backend class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IndexBackend(ABC):
    """Abstract base class for vector index backends."""
    
    @abstractmethod
    async def insert(
        self,
        id: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Insert a vector into the index.
        
        Args:
            id: Unique identifier
            vector: Embedding vector
            metadata: Associated metadata
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        similarity_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            filters: Optional metadata filters
            
        Returns:
            List of results with id, score, and metadata
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a vector from the index.
        
        Args:
            id: Vector identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count vectors in the index.
        
        Args:
            filters: Optional metadata filters
            
        Returns:
            Number of vectors matching filters
        """
        pass
