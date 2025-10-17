"""
Pydantic-powered application settings with YAML + environment variable support.

This module centralizes configuration loading for Atoms MCP using
``pydantic-settings``. It provides strongly-typed access to all settings
with YAML defaults and environment variable overrides.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    Field,
    SecretStr,
    ValidationError,
    computed_field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_ENV_FILES: tuple[str, ...] = (".env", ".env.local")
_DEFAULT_CONFIG_ENV_VAR = "ATOMS_SETTINGS_FILE"
_DEFAULT_CONFIG_FILENAME = "config.yaml"


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Load settings defaults from a YAML file."""

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls)
        custom_path = os.getenv(_DEFAULT_CONFIG_ENV_VAR)
        if custom_path:
            self.yaml_path = Path(custom_path).expanduser()
        else:
            self.yaml_path = Path(__file__).resolve().parent / _DEFAULT_CONFIG_FILENAME

    def get_field_value(
        self, field: Any, field_name: str
    ) -> tuple[Any, str, bool]:
        """Get field value from YAML data."""
        data = self._load_yaml()

        # Navigate nested paths (e.g., 'server.port')
        keys = field_name.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None, field_name, False

        # Check if this is a complex type
        is_complex = isinstance(value, (dict, list))

        # Prepare the field value
        if is_complex:
            prepared = value
        else:
            prepared = self.prepare_field_value(field_name, field, value, False)

        return prepared, field_name, is_complex

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML configuration file."""
        if not self.yaml_path.exists():
            return {}

        try:
            with self.yaml_path.open("r", encoding="utf-8") as stream:
                data = yaml.safe_load(stream) or {}
        except Exception:
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    def __call__(self) -> dict[str, Any]:
        """Return complete YAML data."""
        return self._load_yaml()


class AppBaseSettings(BaseSettings):
    """Shared configuration for all settings models."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ============================================================================
# Server Settings
# ============================================================================


class ServerSettings(AppBaseSettings):
    """Server configuration."""

    name: str = Field(
        default="atoms-fastmcp-consolidated",
        validation_alias=AliasChoices("SERVER_NAME", "ATOMS_SERVER_NAME"),
    )
    transport: Literal["stdio", "http", "sse"] = Field(
        default="http",
        validation_alias=AliasChoices("ATOMS_FASTMCP_TRANSPORT", "TRANSPORT"),
    )
    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("ATOMS_FASTMCP_HOST", "HOST"),
    )
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("ATOMS_FASTMCP_PORT", "PORT"),
    )
    http_path: str = Field(
        default="/api/mcp",
        validation_alias=AliasChoices("ATOMS_FASTMCP_HTTP_PATH"),
    )
    base_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("ATOMS_FASTMCP_BASE_URL"),
    )
    public_base_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("ATOMS_FASTMCP_PUBLIC_BASE_URL"),
    )
    vercel_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VERCEL_URL"),
    )
    reload_server: bool = Field(
        default=False,
        validation_alias=AliasChoices("ATOMS_FASTMCP_RELOAD", "RELOAD"),
    )
    http_auth_mode: Literal["optional", "required"] = Field(
        default="required",
        validation_alias=AliasChoices("ATOMS_FASTMCP_HTTP_AUTH_MODE"),
    )
    environment: str = Field(
        default="production",
        validation_alias=AliasChoices(
            "ATOMS_MCP_ENVIRONMENT",
            "ATOMS_TARGET_ENVIRONMENT",
            "ENV",
        ),
    )

    @field_validator("port")
    @classmethod
    def _ensure_valid_port(cls, value: int) -> int:
        if not (0 < value < 65536):
            raise ValueError("Port must be between 1 and 65535")
        return value

    @field_validator("http_path")
    @classmethod
    def _normalize_http_path(cls, value: str) -> str:
        value = value.strip() or "/api/mcp"
        return value if value.startswith("/") else f"/{value}"


# ============================================================================
# KINFRA Settings
# ============================================================================


class KInfraSettings(AppBaseSettings):
    """KINFRA infrastructure configuration."""

    enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("KINFRA_ENABLED"),
    )
    project_name: str = Field(
        default="atoms-mcp",
        validation_alias=AliasChoices("KINFRA_PROJECT_NAME"),
    )
    preferred_port: int = Field(
        default=8100,
        validation_alias=AliasChoices("KINFRA_PREFERRED_PORT"),
    )
    enable_tunnel: bool = Field(
        default=False,
        validation_alias=AliasChoices("KINFRA_ENABLE_TUNNEL"),
    )
    enable_fallback: bool = Field(
        default=False,
        validation_alias=AliasChoices("KINFRA_ENABLE_FALLBACK"),
    )
    config_dir: str | None = Field(
        default=None,
        validation_alias=AliasChoices("KINFRA_CONFIG_DIR"),
    )


# ============================================================================
# FastMCP Settings
# ============================================================================


class FastMCPSettings(AppBaseSettings):
    """FastMCP-specific configuration."""

    rate_limit_rpm: int = Field(
        default=120,
        validation_alias=AliasChoices("MCP_RATE_LIMIT_RPM"),
    )
    max_concurrent_requests: int = Field(
        default=10,
        validation_alias=AliasChoices("MCP_MAX_CONCURRENT_REQUESTS"),
    )
    request_timeout_seconds: int = Field(
        default=30,
        validation_alias=AliasChoices("MCP_REQUEST_TIMEOUT_SECONDS"),
    )
    enable_compression: bool = Field(
        default=True,
        validation_alias=AliasChoices("MCP_ENABLE_COMPRESSION"),
    )
    enable_cors: bool = Field(
        default=True,
        validation_alias=AliasChoices("MCP_ENABLE_CORS"),
    )


# ============================================================================
# Auth Settings
# ============================================================================


class AuthKitSettings(AppBaseSettings):
    """WorkOS AuthKit configuration."""

    domain: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN",
            "AUTHKIT_DOMAIN",
        ),
    )
    base_url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL",
            "ATOMS_FASTMCP_BASE_URL",
        ),
    )
    required_scopes: tuple[str, ...] = Field(
        default=(),
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES",
            "AUTHKIT_REQUIRED_SCOPES",
        ),
    )

    @field_validator("required_scopes", mode="before")
    @classmethod
    def _parse_scopes(cls, value: object) -> tuple[str, ...]:
        if not value:
            return ()
        if isinstance(value, str):
            return tuple(
                scope.strip()
                for scope in value.replace(" ", ",").split(",")
                if scope.strip()
            )
        if isinstance(value, (list, tuple, set)):
            return tuple(str(scope).strip() for scope in value if str(scope).strip())
        return (str(value).strip(),)


class WorkOSSettings(AppBaseSettings):
    """WorkOS API configuration."""

    api_url: AnyHttpUrl = Field(
        default="https://api.workos.com",
        validation_alias=AliasChoices("WORKOS_API_URL"),
    )
    api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("WORKOS_API_KEY"),
    )
    client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WORKOS_CLIENT_ID"),
    )


class AuthSettings(AppBaseSettings):
    """Authentication and authorization configuration."""

    authkit: AuthKitSettings = Field(default_factory=AuthKitSettings)
    workos: WorkOSSettings = Field(default_factory=WorkOSSettings)


# ============================================================================
# Database Settings
# ============================================================================


class SupabaseSettings(AppBaseSettings):
    """Supabase connection configuration."""

    url: AnyHttpUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    service_role_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_KEY",
        ),
    )
    anon_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        ),
    )
    project_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_PROJECT_ID"),
    )
    db_password: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPABASE_DB_PASSWORD"),
    )
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)

    @computed_field
    @property
    def is_configured(self) -> bool:
        """Return True when the service role credentials are present."""
        return bool(self.url and self.service_role_key)


class DatabaseSettings(AppBaseSettings):
    """Database configuration."""

    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)


# ============================================================================
# API Keys Settings
# ============================================================================


class GoogleCloudSettings(AppBaseSettings):
    """Google Cloud configuration."""

    project: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_CLOUD_PROJECT"),
    )
    location: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_CLOUD_LOCATION"),
    )
    credentials_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_APPLICATION_CREDENTIALS"),
    )


class VertexSettings(AppBaseSettings):
    """Vertex AI configuration."""

    embeddings_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VERTEX_EMBEDDINGS_MODEL"),
    )
    chat_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices("VERTEX_CHAT_MODEL"),
    )


class APIKeysSettings(AppBaseSettings):
    """API keys and secrets configuration."""

    claude_provider: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CLAUDE_PROVIDER"),
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY"),
    )
    google_cloud: GoogleCloudSettings = Field(default_factory=GoogleCloudSettings)
    vertex: VertexSettings = Field(default_factory=VertexSettings)


# ============================================================================
# Feature Flags
# ============================================================================


class FeatureSettings(AppBaseSettings):
    """Feature flag configuration."""

    enable_rag: bool = Field(default=True)
    enable_vector_search: bool = Field(default=True)
    enable_workspace_context: bool = Field(default=True)
    enable_entity_resolver: bool = Field(default=True)
    enable_relationship_graph: bool = Field(default=True)
    enable_workflow_execution: bool = Field(default=True)
    enable_session_persistence: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)


# ============================================================================
# Logging Settings
# ============================================================================


class LoggingSettings(AppBaseSettings):
    """Logging configuration."""

    level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL"),
    )
    format: Literal["json", "text", "pretty"] = Field(default="text")
    output: Literal["stdout", "stderr", "file"] = Field(default="stdout")
    file_path: str | None = Field(default=None)
    enable_rotation: bool = Field(default=False)
    max_bytes: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)
    log_sql_queries: bool = Field(default=False)
    log_api_requests: bool = Field(default=True)


# ============================================================================
# Performance Settings
# ============================================================================


class PerformanceSettings(AppBaseSettings):
    """Performance and caching configuration."""

    enable_query_cache: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300)
    max_cache_size_mb: int = Field(default=100)
    enable_connection_pooling: bool = Field(default=True)
    enable_request_batching: bool = Field(default=False)


# ============================================================================
# Observability Settings
# ============================================================================


class ObservabilitySettings(AppBaseSettings):
    """Observability and monitoring configuration."""

    enable_health_checks: bool = Field(default=True)
    enable_readiness_checks: bool = Field(default=True)
    enable_liveness_checks: bool = Field(default=True)
    health_check_interval_seconds: int = Field(default=30)
    metrics_port: int = Field(default=9090)
    tracing_endpoint: str | None = Field(default=None)
    tracing_sample_rate: float = Field(default=0.1)


# ============================================================================
# Security Settings
# ============================================================================


class SecuritySettings(AppBaseSettings):
    """Security configuration."""

    enable_rate_limiting: bool = Field(default=True)
    enable_request_validation: bool = Field(default=True)
    enable_response_validation: bool = Field(default=True)
    max_request_size_mb: int = Field(default=10)
    allowed_origins: list[str] = Field(default_factory=list)
    enable_csrf_protection: bool = Field(default=False)
    session_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("SESSION_SECRET_KEY"),
    )
    jwt_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("JWT_SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_minutes: int = Field(default=60)


# ============================================================================
# Development Settings
# ============================================================================


class DevelopmentSettings(AppBaseSettings):
    """Development and debugging configuration."""

    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEBUG"),
    )
    hot_reload: bool = Field(default=False)
    profile: bool = Field(default=False)
    mock_external_apis: bool = Field(default=False)
    seed_test_data: bool = Field(default=False)


# ============================================================================
# Main Settings Class
# ============================================================================


class AppSettings(AppBaseSettings):
    """Top-level application settings with nested configuration."""

    server: ServerSettings = Field(default_factory=ServerSettings)
    kinfra: KInfraSettings = Field(default_factory=KInfraSettings)
    fastmcp: FastMCPSettings = Field(default_factory=FastMCPSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api_keys: APIKeysSettings = Field(default_factory=APIKeysSettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    development: DevelopmentSettings = Field(default_factory=DevelopmentSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources priority."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @computed_field
    @property
    def resolved_base_url(self) -> str | None:
        """Best-effort resolution of the public-facing base URL."""
        if self.server.base_url:
            return str(self.server.base_url).rstrip("/")

        if self.server.public_base_url:
            return self._strip_mcp_suffix(str(self.server.public_base_url))

        if self.auth.authkit.base_url:
            return self._strip_mcp_suffix(str(self.auth.authkit.base_url))

        if self.server.vercel_url:
            guess = f"https://{self.server.vercel_url}".rstrip("/")
            return self._strip_mcp_suffix(guess)

        if self.server.transport == "http":
            return f"http://{self.server.host}:{self.server.port}"

        return None

    @staticmethod
    def _strip_mcp_suffix(value: str) -> str:
        """Remove common MCP suffixes from URLs."""
        cleaned = value.rstrip("/")
        for suffix in ("/api/mcp", "/mcp"):
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)]
        return cleaned

    def to_server_kwargs(self) -> dict[str, object]:
        """Return keyword arguments compatible with ServerConfig."""
        return {
            "name": self.server.name,
            "base_url": self.resolved_base_url,
            "authkit_domain": (
                str(self.auth.authkit.domain) if self.auth.authkit.domain else None
            ),
            "authkit_required_scopes": self.auth.authkit.required_scopes,
            "rate_limit_rpm": self.fastmcp.rate_limit_rpm,
            "transport": self.server.transport,
            "host": self.server.host,
            "port": self.server.port,
            "http_path": self.server.http_path,
        }

    def apply_to_environment(self, *, override: bool = False) -> None:
        """Expose key settings to environment variables for legacy consumers."""
        # Supabase
        if self.database.supabase.url:
            url_str = str(self.database.supabase.url)
            if override or "SUPABASE_URL" not in os.environ:
                os.environ["SUPABASE_URL"] = url_str
            if override or "NEXT_PUBLIC_SUPABASE_URL" not in os.environ:
                os.environ["NEXT_PUBLIC_SUPABASE_URL"] = url_str

        if self.database.supabase.service_role_key:
            key_str = self.database.supabase.service_role_key.get_secret_value()
            if override or "SUPABASE_SERVICE_ROLE_KEY" not in os.environ:
                os.environ["SUPABASE_SERVICE_ROLE_KEY"] = key_str
            if override or "SUPABASE_KEY" not in os.environ:
                os.environ["SUPABASE_KEY"] = key_str

        if self.database.supabase.anon_key:
            anon_str = self.database.supabase.anon_key.get_secret_value()
            if override or "SUPABASE_ANON_KEY" not in os.environ:
                os.environ["SUPABASE_ANON_KEY"] = anon_str
            if override or "NEXT_PUBLIC_SUPABASE_ANON_KEY" not in os.environ:
                os.environ["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = anon_str

        # WorkOS
        if override or "WORKOS_API_URL" not in os.environ:
            os.environ["WORKOS_API_URL"] = str(self.auth.workos.api_url)

        if self.auth.workos.api_key:
            value = self.auth.workos.api_key.get_secret_value()
            if override or "WORKOS_API_KEY" not in os.environ:
                os.environ["WORKOS_API_KEY"] = value

        if self.auth.workos.client_id and (override or "WORKOS_CLIENT_ID" not in os.environ):
            os.environ["WORKOS_CLIENT_ID"] = self.auth.workos.client_id

        # Base URL
        if self.resolved_base_url and (override or "ATOMS_FASTMCP_BASE_URL" not in os.environ):
            os.environ["ATOMS_FASTMCP_BASE_URL"] = self.resolved_base_url

        # AuthKit
        auth_domain = str(self.auth.authkit.domain) if self.auth.authkit.domain else None
        if auth_domain and (override or "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN" not in os.environ):
            os.environ["FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN"] = auth_domain

        # Transport
        transport_vars = {
            "ATOMS_FASTMCP_TRANSPORT": self.server.transport,
            "ATOMS_FASTMCP_HOST": self.server.host,
            "HOST": self.server.host,
            "ATOMS_FASTMCP_PORT": str(self.server.port),
            "PORT": str(self.server.port),
            "ATOMS_FASTMCP_HTTP_PATH": self.server.http_path,
        }
        for key, value in transport_vars.items():
            if override or key not in os.environ:
                os.environ[key] = value

        # Other settings
        if override or "MCP_RATE_LIMIT_RPM" not in os.environ:
            os.environ["MCP_RATE_LIMIT_RPM"] = str(self.fastmcp.rate_limit_rpm)

        if override or "ENV" not in os.environ:
            os.environ["ENV"] = self.server.environment

        if override or "LOG_LEVEL" not in os.environ:
            os.environ["LOG_LEVEL"] = self.logging.level

        if self.api_keys.claude_provider and (override or "CLAUDE_PROVIDER" not in os.environ):
            os.environ["CLAUDE_PROVIDER"] = self.api_keys.claude_provider

        if self.api_keys.google_cloud.project and (override or "GOOGLE_CLOUD_PROJECT" not in os.environ):
            os.environ["GOOGLE_CLOUD_PROJECT"] = self.api_keys.google_cloud.project

        if self.api_keys.google_cloud.location and (override or "GOOGLE_CLOUD_LOCATION" not in os.environ):
            os.environ["GOOGLE_CLOUD_LOCATION"] = self.api_keys.google_cloud.location


@lru_cache
def get_settings() -> AppSettings:
    """Lazy singleton accessor for application settings."""
    try:
        settings = AppSettings()
        settings.apply_to_environment()
        return settings
    except ValidationError as exc:
        errors = exc.errors()
        message = "\n".join(
            f"- {'.'.join(str(x) for x in error['loc'])}: {error['msg']}" for error in errors
        )
        raise RuntimeError(f"Invalid configuration:\n{message}") from exc


def reset_settings_cache() -> None:
    """Clear cached settings so new environment variables are picked up."""
    get_settings.cache_clear()


__all__ = [
    "AppSettings",
    "ServerSettings",
    "KInfraSettings",
    "FastMCPSettings",
    "AuthSettings",
    "DatabaseSettings",
    "APIKeysSettings",
    "FeatureSettings",
    "LoggingSettings",
    "PerformanceSettings",
    "ObservabilitySettings",
    "SecuritySettings",
    "DevelopmentSettings",
    "get_settings",
    "reset_settings_cache",
]
