"""
Atoms MCP Production Settings Configuration using Pydantic Settings and YAML.
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server configuration."""
    environment: str = Field("local", description="Environment (local, staging, production)")
    log_level: str = Field("info", description="Log level")
    debug: bool = Field(False, description="Debug mode")


class KinfraConfig(BaseModel):
    """KINFRA infrastructure configuration."""
    managed: int = Field(1, description="Enable KINFRA management")
    tunnel: int = Field(0, description="Enable CloudFlare tunnel")
    fallback: int = Field(1, description="Enable fallback pages")
    restart: int = Field(1, description="Auto-restart on failure")


class FastMCPConfig(BaseModel):
    """FastMCP configuration."""
    transport: str = Field("http", description="Transport protocol")
    host: str = Field("127.0.0.1", description="Host address")
    port: int = Field(8000, description="Port number")
    base_url: str = Field("https://atomcp.kooshapari.com", description="Base URL")
    http_path: str = Field("/api/mcp", description="HTTP path")
    reload: bool = Field(False, description="Auto-reload")
    http_auth_mode: str = Field("optional", description="HTTP auth mode")


class AuthKitProviderConfig(BaseModel):
    """AuthKit provider configuration."""
    authkit_domain: str = Field(default="localhost:3000", description="AuthKit domain")
    authkit_required_scopes: list[str] = Field(["openid", "profile", "email"], description="Required scopes")


class AuthConfig(BaseModel):
    """Authentication configuration."""
    authkit_provider: AuthKitProviderConfig = Field(default_factory=AuthKitProviderConfig)


class APIKeysConfig(BaseModel):
    """API keys configuration."""
    openai: str | None = Field(None, description="OpenAI API key")
    anthropic: str | None = Field(None, description="Anthropic API key")
    openrouter: str | None = Field(None, description="OpenRouter API key")
    groq: str | None = Field(None, description="Groq API key")


class SupabaseConfig(BaseModel):
    """Supabase configuration."""
    url: str = Field(default="https://localhost:54321", description="Supabase URL")
    key: str = Field(default="dummy-key", description="Supabase anon key")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(default="sqlite:///morph.db", description="Database URL")
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""
    enable_caching: bool = Field(True, description="Enable caching")
    enable_streaming: bool = Field(True, description="Enable streaming")
    enable_tool_use: bool = Field(True, description="Enable tool use")
    enable_logging: bool = Field(True, description="Enable logging")


class ToolsConfig(BaseModel):
    """Tool configuration."""
    timeout: int = Field(30, description="Tool timeout")
    max_retries: int = Field(3, description="Maximum retries")
    retry_delay: int = Field(1, description="Retry delay")


class ObservabilityConfig(BaseModel):
    """Observability configuration."""
    enable_profiling: bool = Field(False, description="Enable profiling")
    enable_tracing: bool = Field(False, description="Enable tracing")
    telemetry_enabled: bool = Field(False, description="Enable telemetry")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field("INFO", description="Log level")
    format: str = Field("json", description="Log format")
    max_size: str = Field("10MB", description="Maximum log size")


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    cache_ttl_seconds: int = Field(600, description="Cache TTL in seconds")
    http_timeout_seconds: int = Field(30, description="HTTP timeout in seconds")
    max_concurrent_requests: int = Field(100, description="Maximum concurrent requests")


class Settings(BaseSettings):
    """Main settings class for Atoms MCP Production."""

    model_config = SettingsConfigDict(
        env_file=None,  # Disable .env file usage
        env_prefix="ATOMS_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_ignore_empty=True,
        env_parse_none_str="None",
        config_file="config.yaml",
        config_file_encoding="utf-8",
    )

    # Configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig)
    kinfra: KinfraConfig = Field(default_factory=KinfraConfig)
    fastmcp: FastMCPConfig = Field(default_factory=FastMCPConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    api_keys: APIKeysConfig = Field(default_factory=APIKeysConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


# Alias for backward compatibility
AppSettings = Settings


def reset_settings_cache() -> None:
    """Reset the settings cache."""
    global settings
    settings = Settings()
