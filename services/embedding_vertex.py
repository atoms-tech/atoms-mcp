"""Vertex AI embedding service (Gemini) for RAG functionality.

Uses Google Cloud Vertex AI's text-embedding-004 model exclusively via REST API.
Uses Application Default Credentials (ADC) for authentication.

Required:
- google-auth package (pip install google-auth)
- httpx package (pip install httpx)
- GOOGLE_CLOUD_PROJECT environment variable
- GOOGLE_CLOUD_LOCATION environment variable (optional, defaults to us-central1)
- ADC configured: gcloud auth application-default login
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, NamedTuple
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Check for required packages
try:
    from google.auth import default
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    import json as json_module
    VERTEX_AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Required packages not installed: {e}")
    logger.warning("Install with: pip install httpx google-auth")
    VERTEX_AI_AVAILABLE = False


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


class VertexAIEmbeddingService:
    """Service for generating Vertex AI embeddings with caching using ADC."""

    def __init__(self, cache_size: int = 1000):
        if not VERTEX_AI_AVAILABLE:
            raise RuntimeError(
                "Required packages not available. Install with:\n"
                "  pip install httpx google-auth\n\n"
                "Also configure ADC:\n"
                "  gcloud auth application-default login"
            )

        # Get project and location from environment
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_VERTEX_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1") or os.getenv("GOOGLE_VERTEX_LOCATION", "us-central1")

        if not project:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT must be set.\n"
                "Example: export GOOGLE_CLOUD_PROJECT=serious-mile-462615-a2"
            )

        # Store project and location
        self.project = project
        self.location = location

        # Initialize credentials from service account JSON env var or ADC
        service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if service_account_json:
            # Load from environment variable (for Vercel serverless)
            try:
                service_account_info = json_module.loads(service_account_json)
                self.credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                logger.info("✅ Using service account from environment variable")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to parse service account JSON from environment: {e}\n\n"
                    "Make sure GOOGLE_SERVICE_ACCOUNT_JSON contains valid JSON"
                ) from e
        else:
            # Fall back to ADC (for local development)
            try:
                self.credentials, self.adc_project = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
                logger.info("✅ Using Application Default Credentials (local dev)")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to get credentials: {e}\n\n"
                    "For Vercel/serverless:\n"
                    "  Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable\n\n"
                    "For local development:\n"
                    "  gcloud auth application-default login"
                ) from e

        # Use Vertex AI aiplatform endpoint with ADC
        # Model: gemini-embedding-001 (3072 dimensions, pre-normalized)
        self.endpoint = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/"
            f"projects/{self.project}/locations/{self.location}/"
            f"publishers/google/models/gemini-embedding-001:predict"
        )

        logger.info(f"✅ Vertex AI initialized: {project}/{location}")

        # In-memory cache
        self.cache: Dict[str, EmbeddingResult] = {}
        self.cache_size = cache_size

        # Persistent cache file for backfill reuse
        self.persistent_cache_file = Path.home() / ".atoms_embedding_cache.json"
        self._load_persistent_cache()

        # Only gemini-embedding-001 is supported
        self.default_model = "gemini-embedding-001"
        self.large_model = self.default_model

    def _load_persistent_cache(self):
        """Load cache from disk if it exists."""
        if self.persistent_cache_file.exists():
            try:
                import json
                with open(self.persistent_cache_file, 'r') as f:
                    data = json.load(f)
                    # Convert back to EmbeddingResult objects
                    for key, val in data.items():
                        self.cache[key] = EmbeddingResult(
                            embedding=val['embedding'],
                            tokens_used=val.get('tokens_used', 0),
                            model=val.get('model', self.default_model),
                            cached=True
                        )
                logger.info(f"✅ Loaded {len(self.cache)} cached embeddings from disk")
            except Exception as e:
                logger.warning(f"Failed to load persistent cache: {e}")

    def _save_persistent_cache(self):
        """Save cache to disk."""
        try:
            import json
            # Convert to JSON-serializable format
            data = {}
            for key, result in self.cache.items():
                data[key] = {
                    'embedding': result.embedding,
                    'tokens_used': result.tokens_used,
                    'model': result.model
                }
            with open(self.persistent_cache_file, 'w') as f:
                json.dump(data, f)
            logger.debug(f"💾 Saved {len(data)} embeddings to persistent cache")
        except Exception as e:
            logger.warning(f"Failed to save persistent cache: {e}")

    def _get_cache_key(self, text: str, model: str, task_type: Optional[str] = None, output_dimensionality: int = 3072) -> str:
        """Generate cache key for text, model, task type, and dimensions."""
        content = f"{model}:{task_type or 'default'}:{output_dimensionality}:{text}"
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
        use_cache: bool = True,
        task_type: Optional[str] = None,
        output_dimensionality: int = 3072
    ) -> EmbeddingResult:
        """Generate embedding for a single text using REST API.

        Args:
            text: Text to embed
            model: Must be gemini-embedding-001 (ignored if different)
            use_cache: Whether to use caching (local + Upstash Redis)
            task_type: Task type for optimization (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
            output_dimensionality: Output dimensions (768, 1536, or 3072), default 3072

        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Only gemini-embedding-001 is supported
        model = self.default_model
        cache_key = self._get_cache_key(text, model, task_type, output_dimensionality)

        # Check in-memory cache first (local)
        if use_cache and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            return EmbeddingResult(
                embedding=cached_result.embedding,
                tokens_used=cached_result.tokens_used,
                model=cached_result.model,
                cached=True
            )
        
        # Check Redis cache (Upstash) if available
        if use_cache:
            try:
                from .embedding_cache import get_embedding_cache
                embedding_cache = await get_embedding_cache()
                redis_embedding = await embedding_cache.get(text, model)
                
                if redis_embedding:
                    logger.debug(f"Cache hit (Upstash) for embedding: {text[:50]}")
                    # Also cache in local memory for fast access
                    self.cache[cache_key] = EmbeddingResult(
                        embedding=redis_embedding,
                        tokens_used=0,
                        model=model,
                        cached=True
                    )
                    return EmbeddingResult(
                        embedding=redis_embedding,
                        tokens_used=0,
                        model=model,
                        cached=True
                    )
            except Exception as e:
                logger.debug(f"Redis embedding cache miss or error: {e}")

        try:
            # Get fresh access token from ADC
            if not self.credentials.valid:
                self.credentials.refresh(Request())

            access_token = self.credentials.token

            # Use REST API with ADC bearer token
            import httpx

            # Update endpoint for gemini-embedding-001
            endpoint = (
                f"https://{self.location}-aiplatform.googleapis.com/v1/"
                f"projects/{self.project}/locations/{self.location}/"
                f"publishers/google/models/gemini-embedding-001:predict"
            )

            # Build request body with task type and output dimensionality
            request_body: Dict[str, Any] = {
                "instances": [{"content": text}]
            }
            
            # Add task_type if provided
            if task_type:
                request_body["instances"][0]["task_type"] = task_type
            
            # Add output dimensionality parameter
            request_body["parameters"] = {
                "outputDimensionality": output_dimensionality
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=request_body,
                    timeout=30.0
                )

                response.raise_for_status()
                data = response.json()

                # Extract embedding from Vertex AI response
                values = data["predictions"][0]["embeddings"]["values"]
                
                # Normalize if 768-dim (3072-dim are pre-normalized by Google)
                if output_dimensionality == 768:
                    magnitude = sum(v * v for v in values) ** 0.5
                    if magnitude > 0:
                        values = [v / magnitude for v in values]

            result = EmbeddingResult(
                embedding=values,
                tokens_used=0,  # REST API does not expose token usage for embeddings
                model=model,
                cached=False,
            )

            if use_cache:
                # Cache locally
                self.cache[cache_key] = result
                self._manage_cache_size()

                # Periodically save to disk (every 100 new embeddings)
                if len(self.cache) % 100 == 0:
                    self._save_persistent_cache()
                
                # Cache in Redis (Upstash) for distributed access
                try:
                    from .embedding_cache import get_embedding_cache
                    embedding_cache = await get_embedding_cache()
                    cache_ttl = int(__import__('os').getenv("CACHE_TTL_EMBEDDING", "86400"))
                    await embedding_cache.set(text, values, model, cache_ttl)
                    logger.debug("Cached embedding to Upstash Redis")
                except Exception as e:
                    logger.debug(f"Failed to cache to Upstash Redis: {e}")

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding (Vertex AI): {str(e)}")
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        use_cache: bool = True,
        batch_size: int = 100
    ) -> BatchEmbeddingResult:
        """Generate embeddings for multiple texts efficiently using REST API.

        Args:
            texts: List of texts to embed
            model: Must be gemini-embedding-001 (ignored if different)
            use_cache: Whether to use caching
            batch_size: Maximum texts per API call

        Returns:
            BatchEmbeddingResult with all embeddings and metadata
        """
        if not texts:
            return BatchEmbeddingResult([], 0, self.default_model, 0)

        # Only gemini-embedding-001 is supported
        model = self.default_model
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

            # Generate embeddings for uncached texts using REST API with ADC
            if uncached_texts:
                try:
                    # Get fresh access token
                    if not self.credentials.valid:
                        self.credentials.refresh(Request())

                    access_token = self.credentials.token

                    import httpx

                    async with httpx.AsyncClient() as client:
                        # Make individual requests for each text
                        for idx, text in enumerate(uncached_texts):
                            response = await client.post(
                                self.endpoint,
                                headers={
                                    "Authorization": f"Bearer {access_token}",
                                    "Content-Type": "application/json"
                                },
                                json={
                                    "instances": [{"content": text}]  # Vertex AI format
                                },
                                timeout=30.0
                            )

                            response.raise_for_status()
                            data = response.json()

                            embedding = data["predictions"][0]["embeddings"]["values"]
                            original_idx = uncached_indices[idx]

                            if use_cache:
                                cache_key = self._get_cache_key(text, model)
                                self.cache[cache_key] = EmbeddingResult(
                                    embedding=embedding,
                                    tokens_used=0,
                                    model=model,
                                    cached=False,
                                )
                            batch_results.append((original_idx, embedding))

                except Exception as e:
                    raise RuntimeError(f"Failed to generate batch embeddings (Vertex AI): {str(e)}")

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
