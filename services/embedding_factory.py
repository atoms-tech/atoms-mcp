"""Embedding service factory - Vertex AI only.

This module provides a single embedding service using Google Vertex AI.
All other providers (OpenAI, mock, etc.) have been removed.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)


def get_embedding_service():
    """
    Get the embedding service.

    In test mode (PYTEST_CURRENT_TEST env var set), returns a mock service.
    Otherwise, uses Vertex AI (requires proper configuration).

    Returns:
        EmbeddingService instance (real or mock)

    Raises:
        RuntimeError: If Vertex AI is not available and not in test mode
    """
    
    # In test mode, return mock service
    if "PYTEST_CURRENT_TEST" in os.environ:
        logger.info("🧪 Using mock embedding service for tests")
        return _get_mock_embedding_service()

    # Check Vertex AI availability
    if not _check_vertex_ai_available():
        raise RuntimeError(
            "Vertex AI is not properly configured. Required:\n"
            "  - GOOGLE_CLOUD_PROJECT environment variable\n"
            "  - Application Default Credentials (ADC)\n"
            "  - httpx and google-auth packages (pip install httpx google-auth)\n\n"
            "Authenticate with ADC:\n"
            "  gcloud auth application-default login\n\n"
            "Or set service account:\n"
            "  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
        )

    # Initialize Vertex AI embedding service
    try:
        from .embedding_vertex import VertexAIEmbeddingService
        logger.info("✅ Initialized Vertex AI embedding service")
        return VertexAIEmbeddingService()
    except Exception as e:
        logger.error(f"❌ Vertex AI embedding service failed to initialize: {e}")
        raise RuntimeError(f"Failed to initialize Vertex AI embeddings: {e}") from e


def _get_mock_embedding_service():
    """Create a mock embedding service for tests."""
    class MockEmbeddingService:
        def __init__(self):
            self.model = "mock-model"
            self.default_model = "mock-model"
        
        async def embed(self, text: str):
            """Return a mock embedding (768-dim vector)."""
            import hashlib
            # Create deterministic embedding from text
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            return [(hash_val + i) % 1000 / 1000.0 for i in range(768)]
        
        async def embed_many(self, texts: list):
            """Return mock embeddings for multiple texts."""
            return [await self.embed(text) for text in texts]
        
        async def generate_embedding(self, text: str, model: str = None):
            """Generate embedding (used by ProgressiveEmbeddingService)."""
            return await self.embed(text)
    
    return MockEmbeddingService()


def _check_vertex_ai_available() -> bool:
    """Check if Vertex AI is available and properly configured."""
    try:
        from google.auth import default

        # Check for required environment variables
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_VERTEX_PROJECT")
        if not project:
            logger.error("❌ Missing GOOGLE_CLOUD_PROJECT environment variable")
            return False

        # Check if ADC is available
        try:
            credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            return True
        except Exception as e:
            logger.error(f"❌ Application Default Credentials not available: {e}")
            return False

    except ImportError as e:
        logger.error(f"❌ Required packages not installed: {e}")
        logger.error("   Install with: pip install httpx google-auth")
        return False
