"""Embedding service factory that chooses the best available provider."""

from __future__ import annotations

import os
from utils.logging_setup import get_logger
from typing import Dict

logger = get_logger(__name__)


def get_embedding_service():
    """
    Get the Vertex AI embedding service (gemini-embedding-001).

    Only Vertex AI with gemini-embedding-001 is supported.
    Raises RuntimeError if Vertex AI is not properly configured.

    Returns:
        EmbeddingService instance

    Raises:
        RuntimeError: If Vertex AI is not available or fails to initialize
    """

    # Check Vertex AI availability
    if not _check_vertex_ai_available():
        raise RuntimeError(
            "Vertex AI is not properly configured. Required:\n"
            "  - GOOGLE_CLOUD_PROJECT environment variable\n"
            "  - GOOGLE_APPLICATION_CREDENTIALS or gcloud auth\n"
            "  - vertexai Python package installed"
        )

    # Initialize Vertex AI embedding service
    try:
        from .embedding_vertex import VertexAIEmbeddingService
        logger.info("Using Vertex AI embedding service (gemini-embedding-001)")
        return VertexAIEmbeddingService()
    except Exception as e:
        logger.error(f"Vertex AI embedding service failed to initialize: {e}")
        raise RuntimeError(f"Failed to initialize Vertex AI embeddings: {e}") from e


def _check_vertex_ai_available() -> bool:
    """Check if Vertex AI is available and properly configured."""
    import importlib.util
    
    try:
        # Check if vertexai module is available
        if importlib.util.find_spec("vertexai") is None:
            return False
        
        # Check for required environment variables
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if not project:
            logger.debug("Vertex AI: Missing GOOGLE_CLOUD_PROJECT environment variable")
            return False
        
        # Check for authentication
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not creds_path and not creds_json and not _check_gcloud_auth():
            logger.debug("Vertex AI: No authentication configured")
            return False

        return True
    except (ImportError, ValueError):
        logger.debug("Vertex AI: vertexai package not installed")
        return False


def _check_gcloud_auth() -> bool:
    """Check if gcloud Application Default Credentials are available."""
    try:
        from google.auth import default
        creds, project = default()
        return bool(creds and project)
    except Exception:
        return False


def get_available_providers() -> Dict[str, bool]:
    """Get status of all embedding providers."""
    return {
        "vertex_ai": _check_vertex_ai_available(),
        "mock": True,  # Always available for development
    }
