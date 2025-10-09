"""Embedding providers for Vector-Kit."""

from vector_kit.providers.factory import get_embedding_service
from vector_kit.providers.base import EmbeddingProvider

__all__ = ["get_embedding_service", "EmbeddingProvider"]
