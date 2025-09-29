"""Embedding service factory that chooses the best available provider."""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_embedding_service():
    """
    Get the best available embedding service based on installed dependencies and configuration.
    
    Priority order:
    1. Vertex AI (Google Cloud) - if vertexai package is available
    2. OpenAI - if openai package is available  
    3. Hugging Face - if transformers package is available
    4. Mock service - for testing/development
    
    Returns:
        EmbeddingService instance
    """
    
    # Try Vertex AI first (preferred for production)
    if _check_vertex_ai_available():
        try:
            from .embedding_vertex import VertexAIEmbeddingService
            logger.info("Using Vertex AI embedding service")
            return VertexAIEmbeddingService()
        except Exception as e:
            logger.warning(f"Vertex AI embedding service failed to initialize: {e}")
    
    # Try OpenAI as fallback
    if _check_openai_available():
        try:
            from .embedding_openai import OpenAIEmbeddingService
            logger.info("Using OpenAI embedding service")
            return OpenAIEmbeddingService()
        except Exception as e:
            logger.warning(f"OpenAI embedding service failed to initialize: {e}")
    
    # Try Hugging Face local embeddings
    if _check_huggingface_available():
        try:
            from .embedding_huggingface import HuggingFaceEmbeddingService
            logger.info("Using Hugging Face embedding service")
            return HuggingFaceEmbeddingService()
        except Exception as e:
            logger.warning(f"Hugging Face embedding service failed to initialize: {e}")
    
    # Fallback to mock service for development
    logger.warning("No embedding providers available, using mock service")
    from .embedding_mock import MockEmbeddingService
    return MockEmbeddingService()


def _check_vertex_ai_available() -> bool:
    """Check if Vertex AI is available and properly configured."""
    try:
        import vertexai
        
        # Check for required environment variables
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if not project:
            logger.debug("Vertex AI: Missing GOOGLE_CLOUD_PROJECT environment variable")
            return False
        
        # Check for authentication
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path and not _check_gcloud_auth():
            logger.debug("Vertex AI: No authentication configured")
            return False
        
        return True
    except ImportError:
        logger.debug("Vertex AI: vertexai package not installed")
        return False


def _check_openai_available() -> bool:
    """Check if OpenAI is available and configured."""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.debug("OpenAI: Missing OPENAI_API_KEY environment variable")
            return False
        
        return True
    except ImportError:
        logger.debug("OpenAI: openai package not installed")
        return False


def _check_huggingface_available() -> bool:
    """Check if Hugging Face transformers is available."""
    try:
        import transformers
        import torch
        return True
    except ImportError:
        logger.debug("Hugging Face: transformers or torch package not installed")
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
        "openai": _check_openai_available(), 
        "huggingface": _check_huggingface_available(),
        "mock": True  # Always available
    }