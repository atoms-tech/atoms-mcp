"""
Secondary adapters (outbound integrations).

This module provides implementations of outbound ports for external
services and infrastructure:

- Supabase: Database repository implementation
- Vertex AI: Google Cloud AI services (embeddings, LLM)
- Pheno SDK: Optional logging and tunneling (graceful fallback)
- Cache: In-memory and Redis cache implementations

All adapters implement domain ports and are swappable via dependency injection.
"""

# Supabase exports
from atoms_mcp.adapters.secondary.supabase import (
    SupabaseConnection,
    SupabaseConnectionError,
    SupabaseRepository,
    get_client,
    get_client_with_retry,
    get_connection,
    reset_connection,
)

# Vertex AI exports
from atoms_mcp.adapters.secondary.vertex import (
    ConversationManager,
    EmbeddingError,
    LLMError,
    LLMPrompt,
    TextEmbedder,
    VertexAIClient,
    VertexAIClientError,
    get_client as get_vertex_client,
    reset_client as reset_vertex_client,
)

# Pheno SDK exports (with fallback)
from atoms_mcp.adapters.secondary.pheno import (
    PHENO_AVAILABLE,
    get_logger,
    get_pheno_instance,
    get_tunnel_provider,
    is_pheno_available,
)

# Cache exports
from atoms_mcp.adapters.secondary.cache import (
    Cache,
    CacheFactory,
    MemoryCache,
    RedisCache,
    RedisCacheError,
    get_cache,
    reset_cache,
)

__all__ = [
    # Supabase
    "SupabaseConnection",
    "SupabaseConnectionError",
    "SupabaseRepository",
    "get_client",
    "get_client_with_retry",
    "get_connection",
    "reset_connection",
    # Vertex AI
    "VertexAIClient",
    "VertexAIClientError",
    "get_vertex_client",
    "reset_vertex_client",
    "TextEmbedder",
    "EmbeddingError",
    "LLMPrompt",
    "LLMError",
    "ConversationManager",
    # Pheno SDK
    "PHENO_AVAILABLE",
    "get_logger",
    "get_tunnel_provider",
    "is_pheno_available",
    "get_pheno_instance",
    # Cache
    "Cache",
    "CacheFactory",
    "MemoryCache",
    "RedisCache",
    "RedisCacheError",
    "get_cache",
    "reset_cache",
]
