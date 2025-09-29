"""OpenAI embedding service alternative to Vertex AI."""

from __future__ import annotations

import hashlib
import os
import logging
from typing import Dict, List, Optional, NamedTuple

logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("openai package not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False


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


class OpenAIEmbeddingService:
    """OpenAI embedding service using text-embedding-3-small or ada-002."""
    
    def __init__(self, api_key: Optional[str] = None, cache_size: int = 1000):
        if not OPENAI_AVAILABLE:
            raise RuntimeError(
                "OpenAI not available. Install with: pip install openai"
            )
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable must be set")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.cache: Dict[str, EmbeddingResult] = {}
        self.cache_size = cache_size
        
        # Default to newer model, fallback to ada-002
        self.default_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.large_model = "text-embedding-3-large"
        
        logger.info(f"Initialized OpenAI Embedding Service with model: {self.default_model}")
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
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
        """Generate embedding using OpenAI API."""
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
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=model
            )
            
            embedding = response.data[0].embedding
            tokens_used = response.usage.total_tokens
            
            result = EmbeddingResult(
                embedding=embedding,
                tokens_used=tokens_used,
                model=model,
                cached=False
            )
            
            if use_cache:
                self.cache[cache_key] = result
                self._manage_cache_size()
            
            logger.debug(f"Generated OpenAI embedding ({len(text)} chars, {tokens_used} tokens)")
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate OpenAI embedding: {str(e)}")
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        use_cache: bool = True,
        batch_size: int = 100
    ) -> BatchEmbeddingResult:
        """Generate embeddings for multiple texts efficiently."""
        if not texts:
            return BatchEmbeddingResult([], 0, model or self.default_model, 0)
        
        model = model or self.default_model
        all_embeddings = []
        total_tokens = 0
        cached_count = 0
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            # Check cache for each text in batch
            uncached_texts = []
            uncached_indices = []
            
            for j, text in enumerate(batch_texts):
                if not text.strip():
                    continue
                    
                cache_key = self._get_cache_key(text, model)
                if use_cache and cache_key in self.cache:
                    cached_result = self.cache[cache_key]
                    batch_results.append((j, cached_result.embedding))
                    total_tokens += cached_result.tokens_used
                    cached_count += 1
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(j)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                try:
                    response = self.client.embeddings.create(
                        input=uncached_texts,
                        model=model
                    )
                    
                    batch_tokens = response.usage.total_tokens
                    total_tokens += batch_tokens
                    
                    # Cache and collect results
                    for idx, (original_idx, embedding_data) in enumerate(zip(uncached_indices, response.data)):
                        embedding = embedding_data.embedding
                        if use_cache:
                            cache_key = self._get_cache_key(uncached_texts[idx], model)
                            self.cache[cache_key] = EmbeddingResult(
                                embedding=embedding,
                                tokens_used=batch_tokens // len(uncached_texts),  # Estimate per text
                                model=model,
                                cached=False
                            )
                        batch_results.append((original_idx, embedding))
                        
                except Exception as e:
                    raise RuntimeError(f"Failed to generate batch embeddings (OpenAI): {str(e)}")
            
            # Sort results by original order and add to all_embeddings
            batch_results.sort(key=lambda x: x[0])
            all_embeddings.extend([result[1] for result in batch_results])
        
        if use_cache:
            self._manage_cache_size()
        
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