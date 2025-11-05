"""
Vertex AI adapter module.

This module provides Google Vertex AI implementations for embeddings
and LLM operations.
"""

from atoms_mcp.adapters.secondary.vertex.client import (
    VertexAIClient,
    VertexAIClientError,
    get_client,
    reset_client,
)
from atoms_mcp.adapters.secondary.vertex.embeddings import (
    EmbeddingError,
    TextEmbedder,
)
from atoms_mcp.adapters.secondary.vertex.llm import (
    ConversationManager,
    LLMError,
    LLMPrompt,
)

__all__ = [
    "VertexAIClient",
    "VertexAIClientError",
    "get_client",
    "reset_client",
    "TextEmbedder",
    "EmbeddingError",
    "LLMPrompt",
    "LLMError",
    "ConversationManager",
]
