"""Vertex AI embeddings using REST API (lightweight for serverless).

This service uses the Vertex AI REST API directly instead of the heavy
google-cloud-aiplatform SDK, making it suitable for Vercel serverless deployments.

Size: ~2MB (google-auth) vs 200MB+ (google-cloud-aiplatform)
"""

from __future__ import annotations

import os
import asyncio
import hashlib
import logging
import json
from typing import Optional, NamedTuple
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingResult(NamedTuple):
    """Result from embedding generation."""
    embedding: list[float]
    tokens_used: int
    model: str
    cached: bool = False


class VertexAIRestEmbeddingService:
    """Lightweight Vertex AI embedding service using REST API."""
    
    def __init__(
        self,
        model: str = "text-embedding-004",
        project: Optional[str] = None,
        location: Optional[str] = None,
        cache_dir: Optional[str] = None,
        max_cache_size: int = 10000
    ):
        """Initialize Vertex AI REST embedding service.
        
        Args:
            model: Embedding model to use (text-embedding-004, gemini-embedding-001)
            project: Google Cloud project ID
            location: Google Cloud location (e.g., us-central1)
            cache_dir: Directory for persistent cache
            max_cache_size: Maximum number of embeddings to cache
        """
        self.model = model
        self.project = project or os.getenv("GOOGLE_VERTEX_PROJECT")
        self.location = location or os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")
        
        if not self.project:
            raise ValueError("GOOGLE_VERTEX_PROJECT environment variable or project parameter required")
        
        # Build endpoint URL
        self.endpoint = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project}/locations/{self.location}/"
            f"publishers/google/models/{model}:predict"
        )
        
        # Setup cache
        self.cache: dict[str, EmbeddingResult] = {}
        self.max_cache_size = max_cache_size
        
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "atoms-mcp" / "embeddings-vertex"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"cache_{model.replace('/', '_')}.json"
        
        # Load persistent cache
        self._load_persistent_cache()
        
        # Initialize credentials (lazy)
        self._credentials = None
        self._token = None
        
        logger.info(f"Initialized Vertex AI REST embedding service: {model} @ {self.location}")
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_persistent_cache(self):
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.cache[key] = EmbeddingResult(
                            embedding=value['embedding'],
                            tokens_used=value['tokens_used'],
                            model=value['model'],
                            cached=True
                        )
                logger.info(f"Loaded {len(self.cache)} embeddings from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
    
    def _save_persistent_cache(self):
        """Save cache to disk."""
        try:
            data = {
                key: {
                    'embedding': result.embedding,
                    'tokens_used': result.tokens_used,
                    'model': result.model
                }
                for key, result in self.cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            logger.debug(f"Saved {len(self.cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _manage_cache_size(self):
        """Evict oldest entries if cache exceeds max size."""
        if len(self.cache) > self.max_cache_size:
            remove_count = len(self.cache) // 10
            keys_to_remove = list(self.cache.keys())[:remove_count]
            for key in keys_to_remove:
                del self.cache[key]
    
    async def _get_access_token(self) -> str:
        """Get Google Cloud access token."""
        try:
            from google.auth import default
            from google.auth.transport.requests import Request
            
            if self._credentials is None:
                self._credentials, _ = await asyncio.to_thread(default)
            
            if not self._credentials.valid:
                await asyncio.to_thread(self._credentials.refresh, Request())
            
            return self._credentials.token
            
        except ImportError:
            raise ImportError(
                "google-auth package required. Install with: pip install google-auth"
            )
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> EmbeddingResult:
        """Generate embedding for a single text using Vertex AI REST API.
        
        Args:
            text: Text to embed
            model: Model to use (defaults to instance model)
            use_cache: Whether to use caching
            
        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        model = model or self.model
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
            import httpx
            
            # Get access token
            token = await self._get_access_token()
            
            # Make REST API call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "instances": [{"content": text}]
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract embedding
                embedding = data["predictions"][0]["embeddings"]["values"]
                
                result = EmbeddingResult(
                    embedding=embedding,
                    tokens_used=0,  # REST API doesn't return token count
                    model=model,
                    cached=False
                )
                
                # Cache result
                if use_cache:
                    self.cache[cache_key] = result
                    self._manage_cache_size()
                    
                    # Periodically save to disk
                    if len(self.cache) % 100 == 0:
                        self._save_persistent_cache()
                
                return result
                
        except ImportError:
            raise ImportError(
                "httpx package required. Install with: pip install httpx"
            )
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

