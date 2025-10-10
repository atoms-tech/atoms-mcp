"""
Vector search and embedding configuration for Atoms MCP.

Creates and configures vector search components using pheno-sdk/vector-kit.
"""

import sys
from pathlib import Path

# Add pheno-sdk to path
_repo_root = Path(__file__).resolve().parents[2]
_vector_kit_path = _repo_root / "pheno-sdk" / "vector-kit"

if _vector_kit_path.exists():
    sys.path.insert(0, str(_vector_kit_path))

# Import from pheno-sdk/vector-kit
from vector_kit.pipelines.progressive import ProgressiveEmbeddingService  # noqa: E402
from vector_kit.providers.factory import (  # noqa: E402
    get_embedding_service as _get_embedding_service,
)
from vector_kit.search.enhanced import EnhancedVectorSearchService  # noqa: E402
from vector_kit.search.vector_search import VectorSearchService  # noqa: E402

# Import Supabase client
from supabase_client import get_supabase  # noqa: E402

# Singleton instances
_embedding_service = None
_vector_search_service = None
_enhanced_vector_search_service = None
_progressive_embedding_service = None


def get_embedding_service():
    """
    Get configured embedding service.

    Uses pheno-sdk's Vertex AI embedding service (gemini-embedding-001).

    Returns:
        VertexAIEmbeddingService instance

    Examples:
        >>> from config.vector import get_embedding_service
        >>> embedder = get_embedding_service()
        >>> result = await embedder.generate_embedding("Hello world")
        >>> print(f"Embedding dimension: {len(result.embedding)}")
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = _get_embedding_service()

    return _embedding_service


def get_vector_search_service(supabase_client=None):
    """
    Get configured vector search service.

    Uses pheno-sdk's VectorSearchService for semantic and keyword search.

    Args:
        supabase_client: Optional Supabase client (will auto-initialize if not provided)

    Returns:
        VectorSearchService instance

    Examples:
        >>> from config.vector import get_vector_search_service
        >>> search = get_vector_search_service()
        >>> results = await search.semantic_search(
        ...     "machine learning frameworks",
        ...     similarity_threshold=0.7,
        ...     limit=10
        ... )
    """
    global _vector_search_service

    if _vector_search_service is None:
        client = supabase_client or get_supabase()
        embedding_service = get_embedding_service()
        _vector_search_service = VectorSearchService(client, embedding_service)

    return _vector_search_service


def get_enhanced_vector_search_service(supabase_client=None):
    """
    Get configured enhanced vector search service.

    Uses pheno-sdk's EnhancedVectorSearchService with automatic on-demand
    embedding generation for records without embeddings.

    Args:
        supabase_client: Optional Supabase client (will auto-initialize if not provided)

    Returns:
        EnhancedVectorSearchService instance

    Examples:
        >>> from config.vector import get_enhanced_vector_search_service
        >>> search = get_enhanced_vector_search_service()
        >>> # Automatically generates embeddings for missing records
        >>> results = await search.semantic_search(
        ...     "python frameworks",
        ...     ensure_embeddings=True,
        ...     limit=20
        ... )
    """
    global _enhanced_vector_search_service

    if _enhanced_vector_search_service is None:
        client = supabase_client or get_supabase()
        embedding_service = get_embedding_service()
        _enhanced_vector_search_service = EnhancedVectorSearchService(
            client,
            embedding_service
        )

    return _enhanced_vector_search_service


def get_progressive_embedding_service(supabase_client=None):
    """
    Get configured progressive embedding service.

    Uses pheno-sdk's ProgressiveEmbeddingService for on-demand embedding
    generation during search operations.

    Args:
        supabase_client: Optional Supabase client (will auto-initialize if not provided)

    Returns:
        ProgressiveEmbeddingService instance

    Examples:
        >>> from config.vector import get_progressive_embedding_service
        >>> progressive = get_progressive_embedding_service()
        >>> # Ensure embeddings exist for search
        >>> stats = await progressive.ensure_embeddings_for_search(
        ...     ["document", "requirement"],
        ...     limit=50,
        ...     background=True
        ... )
    """
    global _progressive_embedding_service

    if _progressive_embedding_service is None:
        client = supabase_client or get_supabase()
        embedding_service = get_embedding_service()
        _progressive_embedding_service = ProgressiveEmbeddingService(
            client,
            embedding_service
        )

    return _progressive_embedding_service


def reset_vector_services():
    """
    Reset all vector service singletons.

    Useful for testing or when configuration changes.

    Examples:
        >>> from config.vector import reset_vector_services
        >>> reset_vector_services()
    """
    global _embedding_service, _vector_search_service
    global _enhanced_vector_search_service, _progressive_embedding_service

    _embedding_service = None
    _vector_search_service = None
    _enhanced_vector_search_service = None
    _progressive_embedding_service = None


# Convenience exports
__all__ = [
    "get_embedding_service",
    "get_enhanced_vector_search_service",
    "get_progressive_embedding_service",
    "get_vector_search_service",
    "reset_vector_services",
]

