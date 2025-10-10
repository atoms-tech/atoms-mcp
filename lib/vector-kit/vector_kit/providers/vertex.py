"""Vertex AI embedding service (Gemini) for RAG functionality.

Uses Google Cloud Vertex AI's gemini-embedding-001 model exclusively.
Requires Google ADC credentials or service account JSON via `GOOGLE_APPLICATION_CREDENTIALS`,
and the env vars `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Dict, List, Optional, NamedTuple
import os
from utils.logging_setup import get_logger
from pathlib import Path

logger = get_logger(__name__)

try:
    import vertexai
    try:
        from vertexai.language_models import TextEmbeddingModel  # type: ignore
    except Exception:  # fallback for older SDKs
        from vertexai.preview.language_models import TextEmbeddingModel  # type: ignore
    VERTEX_AI_AVAILABLE = True
except ImportError:
    logger.warning("vertexai package not installed. Install with: pip install google-cloud-aiplatform")
    VERTEX_AI_AVAILABLE = False
    # Create dummy classes for type hints
    class TextEmbeddingModel:
        pass


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
    """Service for generating Vertex AI (Gemini) embeddings with caching."""

    def __init__(self, api_key: Optional[str] = None, cache_size: int = 1000):
        if not VERTEX_AI_AVAILABLE:
            raise RuntimeError(
                "Vertex AI not available. Install with: pip install google-cloud-aiplatform\n"
                "Or use the embedding factory to get an alternative provider."
            )
        
        # api_key is ignored; Vertex AI uses ADC / service account
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT (or GCP_PROJECT) must be set for Vertex AI embeddings")

        # For Vercel serverless: use credentials from JSON env var
        creds_json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        credentials = None
        if creds_json_str:
            try:
                import json
                import tempfile
                from google.oauth2 import service_account

                # Parse JSON and create credentials
                creds_dict = json.loads(creds_json_str)

                # For authorized_user type, use default credentials
                if creds_dict.get("type") == "authorized_user":
                    # Write to temp file for ADC
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                        json.dump(creds_dict, f)
                        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f.name
                    logger.debug("✅ Using Google credentials from env var (authorized_user)")
                else:
                    # Service account credentials
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    logger.debug("✅ Using Google credentials from env var (service_account)")
            except Exception as e:
                logger.warning(f"Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")

        try:
            vertexai.init(project=project, location=location, credentials=credentials)
            logger.debug(f"✅ Vertex AI initialized: {project}/{location}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vertex AI: {e}")

        # In-memory cache
        self.cache: Dict[str, EmbeddingResult] = {}
        self.cache_size = cache_size

        # Persistent cache file for backfill reuse
        self.persistent_cache_file = Path.home() / ".atoms_embedding_cache.json"
        self._load_persistent_cache()

        # Only gemini-embedding-001 is supported
        self.default_model = "gemini-embedding-001"
        self.large_model = self.default_model
        # Cache the model instance to avoid reloading on every call
        self._model_instance = None

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
        """Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Must be gemini-embedding-001 (ignored if different)
            use_cache: Whether to use caching

        Returns:
            EmbeddingResult with embedding vector and metadata
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # Only gemini-embedding-001 is supported
        model = self.default_model
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
            # Use cached model instance to avoid reloading on every call
            if self._model_instance is None:
                self._model_instance = TextEmbeddingModel.from_pretrained(model)

            # Run blocking Vertex AI API call in thread pool to allow true concurrency
            embeddings = await asyncio.to_thread(
                self._model_instance.get_embeddings,
                [text],
                output_dimensionality=768
            )
            values = embeddings[0].values if embeddings else []

            result = EmbeddingResult(
                embedding=values,
                tokens_used=0,  # Vertex API does not expose token usage for embeddings
                model=model,
                cached=False,
            )

            if use_cache:
                self.cache[cache_key] = result
                self._manage_cache_size()

                # Periodically save to disk (every 100 new embeddings)
                if len(self.cache) % 100 == 0:
                    self._save_persistent_cache()

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
        """Generate embeddings for multiple texts efficiently.

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
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                try:
                    model_inst = TextEmbeddingModel.from_pretrained(model)
                    responses = model_inst.get_embeddings(uncached_texts, output_dimensionality=768)

                    # Cache and collect results
                    for idx, (original_idx, emb_obj) in enumerate(zip(uncached_indices, responses)):
                        embedding = emb_obj.values
                        if use_cache:
                            cache_key = self._get_cache_key(uncached_texts[idx], model)
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
