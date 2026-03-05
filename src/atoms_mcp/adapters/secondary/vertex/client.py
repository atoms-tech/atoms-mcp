"""
Google Vertex AI client initialization and configuration.

This module provides client setup for Vertex AI services including
embeddings and LLM models with proper error handling and retry logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from google.cloud import aiplatform
from google.api_core import exceptions as google_exceptions
from google.auth import default as google_auth_default
from google.oauth2 import service_account

from atoms_mcp.infrastructure.config.settings import VertexAISettings, get_settings


class VertexAIClientError(Exception):
    """Exception raised for Vertex AI client errors."""

    pass


class VertexAIClient:
    """
    Manages Google Vertex AI client initialization and configuration.

    This class handles:
    - Client initialization with credentials
    - Project and location configuration
    - Model configuration for embeddings and LLM
    - Error handling and retry logic
    """

    _instance: Optional[VertexAIClient] = None
    _initialized: bool = False
    _settings: Optional[VertexAISettings] = None

    def __new__(cls) -> VertexAIClient:
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize Vertex AI client (only once)."""
        if not self._initialized:
            self._initialize()
            self._initialized = True

    def _initialize(self) -> None:
        """
        Initialize Vertex AI with project configuration.

        Raises:
            VertexAIClientError: If initialization fails
        """
        try:
            settings = get_settings()
            self._settings = settings.vertex_ai

            # Validate required settings
            if not self._settings.project_id:
                raise VertexAIClientError("Vertex AI project_id is not configured")

            # Set up credentials
            credentials = self._get_credentials()

            # Initialize Vertex AI
            aiplatform.init(
                project=self._settings.project_id,
                location=self._settings.location,
                credentials=credentials,
            )

        except Exception as e:
            raise VertexAIClientError(f"Failed to initialize Vertex AI client: {e}") from e

    def _get_credentials(self) -> Optional[service_account.Credentials]:
        """
        Get Google Cloud credentials.

        Returns:
            Credentials object or None to use default credentials

        Raises:
            VertexAIClientError: If credential loading fails
        """
        if not self._settings:
            raise VertexAIClientError("Settings not initialized")

        if self._settings.credentials_path:
            # Load from service account file
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    str(self._settings.credentials_path),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                return credentials
            except Exception as e:
                raise VertexAIClientError(
                    f"Failed to load credentials from {self._settings.credentials_path}: {e}"
                ) from e
        else:
            # Use default credentials (ADC)
            try:
                credentials, project = google_auth_default(
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                return credentials
            except Exception as e:
                raise VertexAIClientError(f"Failed to load default credentials: {e}") from e

    @property
    def project_id(self) -> str:
        """
        Get configured project ID.

        Returns:
            str: GCP project ID

        Raises:
            VertexAIClientError: If not initialized
        """
        if not self._settings:
            raise VertexAIClientError("Client not initialized")
        return self._settings.project_id

    @property
    def location(self) -> str:
        """
        Get configured location.

        Returns:
            str: GCP region

        Raises:
            VertexAIClientError: If not initialized
        """
        if not self._settings:
            raise VertexAIClientError("Client not initialized")
        return self._settings.location

    @property
    def model_name(self) -> str:
        """
        Get configured embedding model name.

        Returns:
            str: Model name

        Raises:
            VertexAIClientError: If not initialized
        """
        if not self._settings:
            raise VertexAIClientError("Client not initialized")
        return self._settings.model_name

    @property
    def max_retries(self) -> int:
        """
        Get maximum retry attempts.

        Returns:
            int: Maximum retries

        Raises:
            VertexAIClientError: If not initialized
        """
        if not self._settings:
            raise VertexAIClientError("Client not initialized")
        return self._settings.max_retries

    @property
    def timeout(self) -> int:
        """
        Get request timeout in seconds.

        Returns:
            int: Timeout in seconds

        Raises:
            VertexAIClientError: If not initialized
        """
        if not self._settings:
            raise VertexAIClientError("Client not initialized")
        return self._settings.timeout

    def is_initialized(self) -> bool:
        """
        Check if client is initialized.

        Returns:
            bool: True if initialized
        """
        return self._initialized

    def reset(self) -> None:
        """
        Reset the client (mainly for testing).

        This clears the initialization state and forces reinitialization
        on the next use.
        """
        self._initialized = False
        self._settings = None


# Global client instance
_client: Optional[VertexAIClient] = None


def get_client() -> VertexAIClient:
    """
    Get the global Vertex AI client instance.

    Returns:
        VertexAIClient: Global client instance
    """
    global _client
    if _client is None:
        _client = VertexAIClient()
    return _client


def reset_client() -> None:
    """Reset global client (mainly for testing)."""
    global _client
    if _client is not None:
        _client.reset()
    _client = None
