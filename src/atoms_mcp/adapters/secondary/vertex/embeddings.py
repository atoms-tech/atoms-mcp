"""
Vertex AI text embedding generation.

This module provides text embedding functionality using Google Vertex AI
with batching, caching, and vector search support.
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional

from google.cloud import aiplatform
from google.api_core import exceptions as google_exceptions
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from atoms_mcp.adapters.secondary.vertex.client import get_client, VertexAIClientError


class EmbeddingError(Exception):
    """Exception raised for embedding generation errors."""

    pass


class TextEmbedder:
    """
    Handles text embedding generation using Vertex AI.

    This class provides:
    - Single and batch text embedding
    - Automatic retry on failures
    - Optional caching of embeddings
    - Support for different embedding tasks (retrieval, classification, etc.)
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_embeddings: bool = False,
        cache: Optional[dict[str, list[float]]] = None,
    ) -> None:
        """
        Initialize text embedder.

        Args:
            model_name: Model name (uses client default if None)
            cache_embeddings: Whether to cache generated embeddings
            cache: Optional external cache dictionary
        """
        self.client = get_client()
        self.model_name = model_name or self.client.model_name
        self.cache_embeddings = cache_embeddings
        self._cache: dict[str, list[float]] = cache or {}

    def _get_model(self) -> TextEmbeddingModel:
        """
        Get the embedding model instance.

        Returns:
            TextEmbeddingModel: Configured model

        Raises:
            EmbeddingError: If model loading fails
        """
        try:
            return TextEmbeddingModel.from_pretrained(self.model_name)
        except Exception as e:
            raise EmbeddingError(f"Failed to load embedding model {self.model_name}: {e}") from e

    def _get_cache_key(self, text: str, task: str) -> str:
        """
        Generate cache key for text and task.

        Args:
            text: Input text
            task: Embedding task type

        Returns:
            Cache key string
        """
        content = f"{text}:{task}:{self.model_name}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate_embedding(
        self,
        text: str,
        task: str = "RETRIEVAL_DOCUMENT",
        title: Optional[str] = None,
    ) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            task: Task type (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
            title: Optional title for document embeddings

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        # Check cache
        if self.cache_embeddings:
            cache_key = self._get_cache_key(text, task)
            if cache_key in self._cache:
                return self._cache[cache_key]

        try:
            model = self._get_model()

            # Create embedding input
            embedding_input = TextEmbeddingInput(
                text=text,
                task_type=task,
                title=title,
            )

            # Generate embedding with retry
            for attempt in range(self.client.max_retries):
                try:
                    embeddings = model.get_embeddings([embedding_input])
                    if embeddings and len(embeddings) > 0:
                        vector = embeddings[0].values

                        # Cache result
                        if self.cache_embeddings:
                            cache_key = self._get_cache_key(text, task)
                            self._cache[cache_key] = vector

                        return vector

                    raise EmbeddingError("Model returned no embeddings")

                except google_exceptions.GoogleAPIError as e:
                    if attempt < self.client.max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise EmbeddingError(f"API error after {attempt + 1} attempts: {e}") from e

            raise EmbeddingError(f"Failed after {self.client.max_retries} attempts")

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def generate_embeddings_batch(
        self,
        texts: list[str],
        task: str = "RETRIEVAL_DOCUMENT",
        titles: Optional[list[str]] = None,
        batch_size: int = 5,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            task: Task type for all texts
            titles: Optional list of titles (must match texts length)
            batch_size: Number of texts per API call (max 5 for Vertex AI)

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If batch embedding fails
        """
        if not texts:
            return []

        if titles and len(titles) != len(texts):
            raise EmbeddingError("Titles list must match texts list length")

        if batch_size > 5:
            batch_size = 5  # Vertex AI limit

        results: list[list[float]] = []

        try:
            model = self._get_model()

            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]
                batch_titles = titles[i : i + batch_size] if titles else None

                # Check cache first
                batch_embeddings: list[Optional[list[float]]] = [None] * len(batch_texts)
                uncached_indices: list[int] = []

                if self.cache_embeddings:
                    for j, text in enumerate(batch_texts):
                        cache_key = self._get_cache_key(text, task)
                        if cache_key in self._cache:
                            batch_embeddings[j] = self._cache[cache_key]
                        else:
                            uncached_indices.append(j)
                else:
                    uncached_indices = list(range(len(batch_texts)))

                # Generate embeddings for uncached items
                if uncached_indices:
                    uncached_texts = [batch_texts[j] for j in uncached_indices]
                    uncached_titles = [batch_titles[j] for j in uncached_indices] if batch_titles else None

                    # Create embedding inputs
                    embedding_inputs = [
                        TextEmbeddingInput(
                            text=uncached_texts[j],
                            task_type=task,
                            title=uncached_titles[j] if uncached_titles else None,
                        )
                        for j in range(len(uncached_texts))
                    ]

                    # Generate with retry
                    for attempt in range(self.client.max_retries):
                        try:
                            embeddings = model.get_embeddings(embedding_inputs)

                            # Update batch results and cache
                            for j, idx in enumerate(uncached_indices):
                                vector = embeddings[j].values
                                batch_embeddings[idx] = vector

                                if self.cache_embeddings:
                                    cache_key = self._get_cache_key(batch_texts[idx], task)
                                    self._cache[cache_key] = vector

                            break

                        except google_exceptions.GoogleAPIError as e:
                            if attempt < self.client.max_retries - 1:
                                time.sleep(2 ** attempt)
                                continue
                            raise EmbeddingError(f"API error in batch {i}: {e}") from e

                # Add batch results
                results.extend([emb for emb in batch_embeddings if emb is not None])

            return results

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()

    def get_cache_size(self) -> int:
        """
        Get number of cached embeddings.

        Returns:
            Number of items in cache
        """
        return len(self._cache)

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension

        Raises:
            EmbeddingError: If dimension cannot be determined
        """
        try:
            # Generate a test embedding
            test_vector = self.generate_embedding("test", task="RETRIEVAL_QUERY")
            return len(test_vector)
        except Exception as e:
            raise EmbeddingError(f"Failed to determine embedding dimension: {e}") from e
