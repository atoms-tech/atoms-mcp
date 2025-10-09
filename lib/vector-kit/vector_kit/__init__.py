"""
Vector-Kit: Unified Embeddings and Vector Search SDK

Provides vendor-agnostic vector search with progressive embedding,
hybrid search, and multi-provider support.

Example:
    ```python
    from vector_kit import VectorClient, EmbeddingProvider, IndexBackend
    
    client = VectorClient(
        provider=EmbeddingProvider.vertex(project="my-project"),
        index=IndexBackend.pgvector(dsn="postgres://..."),
    )
    
    # Progressive semantic search
    results = await client.search.semantic(
        query="machine learning frameworks",
        limit=20,
        ensure_embeddings=True,
    )
    ```
"""

__version__ = "0.1.0"

from vector_kit.client import VectorClient
from vector_kit.providers.base import EmbeddingProvider
from vector_kit.backends.base import IndexBackend
from vector_kit.search.types import SearchResult, SearchResponse

__all__ = [
    "VectorClient",
    "EmbeddingProvider",
    "IndexBackend",
    "SearchResult",
    "SearchResponse",
]
