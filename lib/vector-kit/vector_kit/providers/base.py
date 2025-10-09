"""Base embedding provider class."""

from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched).
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider."""
        pass
