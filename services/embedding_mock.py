"""Mock embedding service for development and testing."""

from __future__ import annotations

import hashlib
import random
from typing import Dict, List, Optional, NamedTuple
import logging

logger = logging.getLogger(__name__)


class EmbeddingResult(NamedTuple):
    """Result of a single embedding operation."""
    embedding: List[float]
    tokens_used: int
    model: str
    cached: bool = False


class BatchEmbeddingResult(NamedTuple):
    """Result of a batch embedding operation."""
    embeddings: List[List[float]]
    total_tokens: int
    model: str
    cached_count: int = 0


class MockEmbeddingService:
    """Mock embedding service that generates deterministic fake embeddings for testing."""
    
    def __init__(self, api_key: Optional[str] = None, cache_size: int = 1000):
        self.cache: Dict[str, EmbeddingResult] = {}
        self.cache_size = cache_size
        self.default_model = "mock-embeddings-768"
        self.embedding_dimension = 768
        
        logger.info("Initialized Mock Embedding Service (for development/testing only)")
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_fake_embedding(self, text: str) -> List[float]:
        """Generate a deterministic fake embedding based on text content."""
        # Use text hash as seed for reproducible embeddings
        seed = hash(text) % 2**31
        random.seed(seed)
        
        # Generate normalized embedding vector
        embedding = [random.gauss(0, 1) for _ in range(self.embedding_dimension)]
        
        # Normalize to unit vector (common for embeddings)
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        return max(1, len(text.split()) * 4 // 3)  # Rough estimate
    
    def _manage_cache_size(self):
        """Remove oldest entries if cache exceeds size limit."""
        if len(self.cache) > self.cache_size:
            # Remove 20% of oldest entries (simple FIFO approach)
            remove_count = int(self.cache_size * 0.2)
            keys_to_remove = list(self.cache.keys())[:remove_count]
            for key in keys_to_remove:
                del self.cache[key]
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """Generate a mock embedding for text."""
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        model = model or self.default_model
        cache_key = self._get_cache_key(text, model)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            return EmbeddingResult(
                embedding=cached_result.embedding,
                tokens_used=cached_result.tokens_used,
                model=cached_result.model,
                cached=True
            )
        
        # Generate fake embedding
        embedding = self._generate_fake_embedding(text)
        tokens_used = self._estimate_tokens(text)
        
        result = EmbeddingResult(
            embedding=embedding,
            tokens_used=tokens_used,
            model=model,
            cached=False
        )
        
        if use_cache:
            self.cache[cache_key] = result
            self._manage_cache_size()
        
        logger.debug(f"Generated mock embedding for text ({len(text)} chars, {tokens_used} tokens)")
        return result
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        use_cache: bool = True,
        batch_size: int = 100
    ) -> BatchEmbeddingResult:
        """Generate mock embeddings for multiple texts."""
        if not texts:
            return BatchEmbeddingResult([], 0, model or self.default_model, 0)
        
        model = model or self.default_model
        all_embeddings = []
        total_tokens = 0
        cached_count = 0
        
        for text in texts:
            if not text.strip():
                continue
            
            result = await self.generate_embedding(text, model, use_cache)
            all_embeddings.append(result.embedding)
            total_tokens += result.tokens_used
            if result.cached:
                cached_count += 1
        
        return BatchEmbeddingResult(
            embeddings=all_embeddings,
            total_tokens=total_tokens,
            model=model,
            cached_count=cached_count
        )
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get current cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_limit": self.cache_size
        }
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.cache.clear()