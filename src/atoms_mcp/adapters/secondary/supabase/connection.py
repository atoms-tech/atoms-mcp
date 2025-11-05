"""
Supabase connection management.

This module handles Supabase client initialization, connection pooling,
and configuration for database operations.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from atoms_mcp.infrastructure.config.settings import DatabaseSettings, get_settings


class SupabaseConnectionError(Exception):
    """Exception raised for Supabase connection errors."""

    pass


class SupabaseConnection:
    """
    Manages Supabase client connection with retry logic and pooling.

    This class provides a singleton pattern for Supabase client management,
    ensuring efficient connection reuse and automatic retry on failures.
    """

    _instance: Optional[SupabaseConnection] = None
    _client: Optional[Client] = None
    _settings: Optional[DatabaseSettings] = None

    def __new__(cls) -> SupabaseConnection:
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize connection manager (only once)."""
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize Supabase client with configuration from settings.

        Raises:
            SupabaseConnectionError: If initialization fails
        """
        try:
            settings = get_settings()
            self._settings = settings.database

            # Validate required settings
            if not self._settings.url:
                raise SupabaseConnectionError("Supabase URL is not configured")
            if not self._settings.api_key:
                raise SupabaseConnectionError("Supabase API key is not configured")

            # Create client options with pooling configuration
            options = ClientOptions(
                schema=self._settings.schema,
                auto_refresh_token=True,
                persist_session=True,
            )

            # Create Supabase client
            self._client = create_client(
                supabase_url=self._settings.url,
                supabase_key=self._settings.api_key,
                options=options,
            )

        except Exception as e:
            raise SupabaseConnectionError(f"Failed to initialize Supabase client: {e}") from e

    def get_client(self) -> Client:
        """
        Get the Supabase client instance.

        Returns:
            Client: Configured Supabase client

        Raises:
            SupabaseConnectionError: If client is not initialized
        """
        if self._client is None:
            raise SupabaseConnectionError("Supabase client is not initialized")
        return self._client

    def get_client_with_retry(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> Client:
        """
        Get Supabase client with automatic retry on connection failures.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for retry delay on each attempt

        Returns:
            Client: Configured Supabase client

        Raises:
            SupabaseConnectionError: If all retry attempts fail
        """
        last_error: Optional[Exception] = None
        delay = retry_delay

        for attempt in range(max_retries):
            try:
                client = self.get_client()
                # Test connection with a simple query
                client.table("_health_check").select("*").limit(1).execute()
                return client
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= backoff_factor
                    # Try to reinitialize client on error
                    self._client = None
                    self._initialize_client()

        raise SupabaseConnectionError(
            f"Failed to connect to Supabase after {max_retries} attempts: {last_error}"
        ) from last_error

    def reset(self) -> None:
        """
        Reset the connection (mainly for testing).

        This clears the cached client instance and forces reinitialization
        on the next connection attempt.
        """
        self._client = None
        self._settings = None

    @property
    def is_connected(self) -> bool:
        """
        Check if client is initialized.

        Returns:
            bool: True if client is initialized, False otherwise
        """
        return self._client is not None


# Global connection instance
_connection: Optional[SupabaseConnection] = None


def get_connection() -> SupabaseConnection:
    """
    Get the global Supabase connection instance.

    Returns:
        SupabaseConnection: Global connection manager
    """
    global _connection
    if _connection is None:
        _connection = SupabaseConnection()
    return _connection


def get_client() -> Client:
    """
    Get Supabase client from global connection.

    Returns:
        Client: Configured Supabase client

    Raises:
        SupabaseConnectionError: If connection fails
    """
    return get_connection().get_client()


def get_client_with_retry(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
) -> Client:
    """
    Get Supabase client with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for retry delay on each attempt

    Returns:
        Client: Configured Supabase client

    Raises:
        SupabaseConnectionError: If all retry attempts fail
    """
    return get_connection().get_client_with_retry(max_retries, retry_delay, backoff_factor)


def reset_connection() -> None:
    """Reset global connection (mainly for testing)."""
    global _connection
    if _connection is not None:
        _connection.reset()
    _connection = None
