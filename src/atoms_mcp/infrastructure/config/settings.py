"""
Configuration settings for Atoms MCP.

This module provides a single, unified configuration class using Pydantic
that replaces the previous 8 separate configuration files. It handles all
settings for database, AI, authentication, caching, logging, and MCP server.

No YAML, no pheno-sdk imports - pure Pydantic with environment variables.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log output format."""

    TEXT = "text"
    JSON = "json"


class CacheBackend(str, Enum):
    """Cache backend type."""

    MEMORY = "memory"
    REDIS = "redis"


class DatabaseSettings(BaseSettings):
    """Database configuration (Supabase)."""

    url: str = Field(
        default="",
        description="Supabase database URL",
    )
    api_key: str = Field(
        default="",
        description="Supabase API key (anon key)",
    )
    service_role_key: str = Field(
        default="",
        description="Supabase service role key (for admin operations)",
    )
    schema: str = Field(
        default="public",
        description="Database schema name",
    )
    pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum database connection pool size",
    )
    pool_timeout: int = Field(
        default=30,
        ge=1,
        description="Connection pool timeout in seconds",
    )
    max_overflow: int = Field(
        default=20,
        ge=0,
        description="Maximum overflow connections beyond pool_size",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)",
    )

    model_config = SettingsConfigDict(
        env_prefix="SUPABASE_",
        case_sensitive=False,
    )

    @field_validator("url", "api_key")
    @classmethod
    def validate_required_fields(cls, v: str, info) -> str:
        """Validate required database fields are not empty."""
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty")
        return v


class VertexAISettings(BaseSettings):
    """Vertex AI configuration for embeddings and AI operations."""

    project_id: str = Field(
        default="",
        description="GCP project ID",
    )
    location: str = Field(
        default="us-central1",
        description="GCP region for Vertex AI",
    )
    model_name: str = Field(
        default="text-embedding-004",
        description="Vertex AI embedding model name",
    )
    api_endpoint: Optional[str] = Field(
        default=None,
        description="Custom API endpoint (optional)",
    )
    credentials_path: Optional[Path] = Field(
        default=None,
        description="Path to GCP service account JSON credentials",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for API calls",
    )
    timeout: int = Field(
        default=30,
        ge=1,
        description="API request timeout in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="VERTEX_AI_",
        case_sensitive=False,
    )

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID is not empty."""
        if not v:
            raise ValueError("project_id cannot be empty")
        return v

    @field_validator("credentials_path")
    @classmethod
    def validate_credentials_path(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate credentials file exists if provided."""
        if v and not v.exists():
            raise ValueError(f"Credentials file not found: {v}")
        return v


class WorkOSSettings(BaseSettings):
    """WorkOS configuration for authentication and organization management."""

    api_key: str = Field(
        default="",
        description="WorkOS API key",
    )
    client_id: str = Field(
        default="",
        description="WorkOS client ID",
    )
    organization_id: Optional[str] = Field(
        default=None,
        description="Default organization ID",
    )
    redirect_uri: str = Field(
        default="http://localhost:3000/auth/callback",
        description="OAuth redirect URI",
    )
    environment: Literal["production", "staging", "development"] = Field(
        default="development",
        description="WorkOS environment",
    )

    model_config = SettingsConfigDict(
        env_prefix="WORKOS_",
        case_sensitive=False,
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v:
            raise ValueError("api_key cannot be empty")
        return v


class PhenoSDKSettings(BaseSettings):
    """Optional Pheno-SDK configuration."""

    enabled: bool = Field(
        default=False,
        description="Enable Pheno-SDK integration",
    )
    tunnel_enabled: bool = Field(
        default=False,
        description="Enable Pheno tunnel for development",
    )
    tunnel_subdomain: Optional[str] = Field(
        default=None,
        description="Custom tunnel subdomain",
    )
    logging_level: Optional[LogLevel] = Field(
        default=None,
        description="Pheno-SDK specific logging level",
    )

    model_config = SettingsConfigDict(
        env_prefix="PHENO_",
        case_sensitive=False,
    )


class CacheSettings(BaseSettings):
    """Cache configuration."""

    backend: CacheBackend = Field(
        default=CacheBackend.MEMORY,
        description="Cache backend type (memory or redis)",
    )
    default_ttl: int = Field(
        default=300,
        ge=0,
        description="Default TTL in seconds (0 = no expiration)",
    )
    max_size: int = Field(
        default=1000,
        ge=1,
        description="Maximum number of items in memory cache",
    )

    # Redis-specific settings
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (redis://host:port/db)",
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host",
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port",
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number",
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password",
    )
    redis_max_connections: int = Field(
        default=10,
        ge=1,
        description="Maximum Redis connection pool size",
    )

    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_redis_settings(self) -> "CacheSettings":
        """Validate Redis settings if Redis backend is selected."""
        if self.backend == CacheBackend.REDIS and not self.redis_url:
            # Build redis_url from components if not provided
            password_part = f":{self.redis_password}@" if self.redis_password else ""
            self.redis_url = (
                f"redis://{password_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )
        return self


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Global logging level",
    )
    format: LogFormat = Field(
        default=LogFormat.TEXT,
        description="Log output format",
    )
    console_enabled: bool = Field(
        default=True,
        description="Enable console logging",
    )
    file_enabled: bool = Field(
        default=False,
        description="Enable file logging",
    )
    file_path: Path = Field(
        default=Path("logs/atoms-mcp.log"),
        description="Log file path",
    )
    file_max_bytes: int = Field(
        default=10485760,  # 10MB
        ge=1024,
        description="Maximum log file size in bytes before rotation",
    )
    file_backup_count: int = Field(
        default=5,
        ge=0,
        le=100,
        description="Number of backup log files to keep",
    )
    include_timestamp: bool = Field(
        default=True,
        description="Include timestamp in log messages",
    )
    include_caller: bool = Field(
        default=False,
        description="Include caller information (file, line) in logs",
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False,
    )

    @field_validator("file_path")
    @classmethod
    def ensure_log_directory(cls, v: Path) -> Path:
        """Ensure log directory exists if file logging is enabled."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


class MCPServerSettings(BaseSettings):
    """MCP server configuration."""

    host: str = Field(
        default="localhost",
        description="Server host address",
    )
    port: int = Field(
        default=8765,
        ge=1024,
        le=65535,
        description="Server port",
    )
    max_workers: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent workers",
    )
    timeout: int = Field(
        default=300,
        ge=1,
        description="Request timeout in seconds",
    )
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    max_request_size: int = Field(
        default=10485760,  # 10MB
        ge=1024,
        description="Maximum request size in bytes",
    )

    model_config = SettingsConfigDict(
        env_prefix="MCP_SERVER_",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """
    Main settings class combining all configuration sections.

    This replaces 8 separate configuration files with a single,
    unified configuration using Pydantic BaseSettings.
    """

    # Application metadata
    app_name: str = Field(
        default="Atoms MCP",
        description="Application name",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Configuration sections
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database configuration",
    )
    vertex_ai: VertexAISettings = Field(
        default_factory=VertexAISettings,
        description="Vertex AI configuration",
    )
    workos: WorkOSSettings = Field(
        default_factory=WorkOSSettings,
        description="WorkOS configuration",
    )
    pheno: PhenoSDKSettings = Field(
        default_factory=PhenoSDKSettings,
        description="Pheno-SDK configuration",
    )
    cache: CacheSettings = Field(
        default_factory=CacheSettings,
        description="Cache configuration",
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration",
    )
    mcp_server: MCPServerSettings = Field(
        default_factory=MCPServerSettings,
        description="MCP server configuration",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def sync_debug_and_logging(self) -> "Settings":
        """Sync debug mode with logging level."""
        if self.debug and self.logging.level != LogLevel.DEBUG:
            self.logging.level = LogLevel.DEBUG
        return self


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: Global configuration instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (mainly for testing)."""
    global _settings
    _settings = None
