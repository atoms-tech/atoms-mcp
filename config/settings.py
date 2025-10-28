"""
Atoms MCP Server Configuration
Uses pydantic settings with environment variable mapping (Pydantic V2 compatible)
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from pydantic import AliasChoices, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database connection secrets."""

    model_config = {"extra": "ignore"}
    url: str = Field(
        default="",
        validation_alias=AliasChoices("url", "DATABASE_URL", "ATOMS_DATABASE_URL"),
    )


class TunnelConfig(BaseSettings):
    """Tunnel configuration settings"""
    model_config = {"env_prefix": "ATOMS_TUNNEL_"}
    auth_token: Optional[str] = Field(default=None)
    account_id: Optional[str] = Field(default=None)
    enabled: bool = Field(default=True)
    hostname: str = Field(default="atomcp.kooshapari.com")
    health_interval: int = Field(default=30)


class ServerConfig(BaseSettings):
    """Server configuration settings"""
    model_config = {"env_prefix": "ATOMS_"}
    host: str = Field(default="0.0.0.0")
    port: int | None = Field(default=None)
    debug: bool = Field(default=False)
    telemetry: bool = Field(default=True)


class FastMCPConfig(BaseSettings):
    """FastMCP configuration settings"""
    model_config = {"env_prefix": "ATOMS_MCP_", "extra": "allow"}
    transport: str = Field(default="stdio")
    host: str = Field(default="127.0.0.1")
    port: int | None = Field(default=None)
    http_path: str = Field(default="/api/mcp")
    base_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_BASE_URL",
            "ATOMS_MCP_BASE_URL",
        ),
    )
    tools: List[str] = Field(default=["entity", "query", "workflow"])
    authkit_domain: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_AUTHKIT_DOMAIN",
            "ATOMS_MCP_AUTHKIT_DOMAIN",
        ),
    )
    authkit_required_scopes: Optional[List[str]] = Field(
        default=None,
        validation_alias=AliasChoices(
            "FASTMCP_SERVER_AUTH_AUTHKITPROVIDER_REQUIRED_SCOPES",
            "ATOMS_MCP_AUTHKIT_REQUIRED_SCOPES",
        ),
    )

    @field_validator("authkit_required_scopes", mode="before")
    @classmethod
    def _normalize_scopes(cls, value: Any) -> Optional[List[str]]:
        """Allow env strings, JSON arrays, or lists."""
        if value is None or value == "" or value == []:
            return None

        if isinstance(value, list):
            return [str(scope).strip() for scope in value if str(scope).strip()]

        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return None

            # Try JSON array/string first
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                return [str(scope).strip() for scope in parsed if str(scope).strip()]
            if isinstance(parsed, str):
                parsed_str = parsed.strip()
                return [parsed_str] if parsed_str else None

            # Fallback: comma or whitespace separated string
            parts = [part.strip() for part in candidate.replace(",", " ").split()]
            return [part for part in parts if part]

        # Fallback to string conversion
        value_str = str(value).strip()
        return [value_str] if value_str else None


class AuthConfig(BaseSettings):
    """HTTP auth configuration for FastMCP."""
    model_config = {"extra": "allow"}
    mode: str = Field(
        default="required",
        validation_alias=AliasChoices("ATOMS_FASTMCP_HTTP_AUTH_MODE", "ATOMS_HTTP_AUTH_MODE"),
    )
    public_base_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias=AliasChoices("ATOMS_FASTMCP_PUBLIC_BASE_URL"),
    )
    server_auth: str = Field(
        default="fastmcp.server.auth.providers.workos.AuthKitProvider",
        validation_alias=AliasChoices("FASTMCP_SERVER_AUTH"),
    )


class SupabaseConfig(BaseSettings):
    """Supabase configuration."""
    model_config = {"extra": "allow"}
    url: str = Field(
        default="https://ydogoylwenufckscqijp.supabase.co",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )


class VertexConfig(BaseSettings):
    """Vertex AI configuration."""
    model_config = {"extra": "allow"}
    project: str = Field(
        default="serious-mile-462615-a2",
        validation_alias=AliasChoices("VERTEX_AI_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    location: str = Field(
        default="us-central1",
        validation_alias=AliasChoices("VERTEX_AI_LOCATION", "GOOGLE_CLOUD_LOCATION"),
    )
    embeddings_model: str = Field(
        default="gemini-embedding-001",
        validation_alias=AliasChoices("VERTEX_EMBEDDINGS_MODEL"),
    )
    use_application_default: bool = Field(
        default=True,
        validation_alias=AliasChoices("VERTEX_AI_USE_APPLICATION_DEFAULT"),
    )
    model_discovery_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("VERTEX_AI_MODEL_DISCOVERY_ENABLED"),
    )
    model_cache_ttl: str = Field(
        default="3600s",
        validation_alias=AliasChoices("VERTEX_AI_MODEL_CACHE_TTL"),
    )


class KinfraConfig(BaseSettings):
    """KInfra configuration settings."""
    model_config = {"env_prefix": "ATOMS_KINFRA_"}
    enabled: bool = Field(default=True)
    project_name: str = Field(default="atoms-mcp")
    preferred_port: int = Field(default=8000)
    domain: str = Field(default="atomcp.kooshapari.com")
    enable_tunnel: bool = Field(default=True)


class ResourcesConfig(BaseSettings):
    """Resource configuration settings"""
    model_config = {"env_prefix": "ATOMS_"}
    max_memory_mb: int = Field(default=512)
    max_connections: int = Field(default=100)
    timeout_seconds: int = Field(default=30)


class LoggingConfig(BaseSettings):
    """Logging configuration settings"""
    model_config = {"env_prefix": "ATOMS_LOG_"}
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    max_file_size_mb: int = Field(default=100)


class HealthConfig(BaseSettings):
    """Health check configuration settings"""
    model_config = {"env_prefix": "ATOMS_HEALTH_"}
    endpoint: str = Field(default="/health")
    timeout_seconds: int = Field(default=5)
    retry_attempts: int = Field(default=3)
    health_interval: int = Field(default=30)


def load_yaml_config(yaml_file: str) -> Dict[str, Any]:
    """Load YAML configuration with environment variable substitution"""
    yaml_filename = yaml_file.replace("config/", "")
    default_path = Path(__file__).parent / yaml_filename

    candidate_paths = [
        default_path,
        Path(__file__).parent / yaml_file,
        Path.cwd() / yaml_file,
    ]

    project_root_env = os.environ.get("ATOMS_PROJECT_ROOT")
    if project_root_env:
        candidate_paths.append(Path(project_root_env) / yaml_file)

    config_path = next((path for path in candidate_paths if path.exists()), None)
    if config_path is None:
        print(f"[ERROR] Config file not found: {default_path}")
        return {}

    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
            # Environment variable substitution with defaults (e.g., ${VAR:-default})
            import re
            def replace_env_var(match):
                var_expr = match.group(1)  # VAR:-default
                if ':-' in var_expr:
                    var_name, default_value = var_expr.split(':-', 1)
                    return os.environ.get(var_name, default_value)
                else:
                    return os.environ.get(var_expr, '')
            
            # Replace ${VAR:-default} patterns
            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
            
            return yaml.safe_load(content) or {}
    except Exception as e:
        print(f"[ERROR] Failed to load {yaml_file}: {e}")
        return {}


class SupabaseSecrets(BaseModel):
    anon_key: str = Field(default="")
    service_role_key: Optional[str] = Field(default=None)


class WorkOSSecrets(BaseModel):
    api_key: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)


class UpstashSecrets(BaseModel):
    rest_url: Optional[str] = Field(default=None)
    rest_token: Optional[str] = Field(default=None)
    redis_url: Optional[str] = Field(default=None)


class ServiceSecrets(BaseModel):
    mcp_secret: Optional[str] = Field(default=None)
    jwt_secret: Optional[str] = Field(default=None)


class SecretsConfig(BaseModel):
    """Sensitive configuration loaded from YAML"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    supabase: SupabaseSecrets = Field(default_factory=SupabaseSecrets)
    workos: WorkOSSecrets = Field(default_factory=WorkOSSecrets)
    upstash: UpstashSecrets = Field(default_factory=UpstashSecrets)
    services: ServiceSecrets = Field(default_factory=ServiceSecrets)


class AppConfig(BaseModel):
    """Main application configuration loaded from YAML"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    tunnel: TunnelConfig = Field(default_factory=TunnelConfig)
    fastmcp: FastMCPConfig = Field(default_factory=FastMCPConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    supabase: SupabaseConfig = Field(default_factory=SupabaseConfig)
    vertex: VertexConfig = Field(default_factory=VertexConfig)
    kinfra: KinfraConfig = Field(default_factory=KinfraConfig)
    resources: ResourcesConfig = Field(default_factory=ResourcesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    health: HealthConfig = Field(default_factory=HealthConfig)


def load_config() -> tuple[AppConfig, SecretsConfig]:
    """Load both configuration files"""
    # Load app config
    app_data = load_yaml_config("config/atoms.config.yaml")
    app_config = AppConfig(**app_data)
    print(f"[DEBUG] Loaded app config from: config/atoms.config.yaml")
    
    # Load secrets config
    secrets_data = load_yaml_config("config/atoms.secrets.yaml")
    secrets_config = SecretsConfig(**secrets_data)
    print(f"[DEBUG] Loaded secrets config from: config/atoms.secrets.yaml")
    
    return app_config, secrets_config


def get_config_summary(app_config: AppConfig, secrets_config: SecretsConfig) -> str:
    """Get formatted configuration summary"""
    return f"""
Configuration Loaded:
├── Server: {app_config.server.host}:{app_config.server.port} (debug={app_config.server.debug})
├── Tunnel: {'enabled' if app_config.tunnel.enabled else 'disabled'} -> {app_config.tunnel.hostname}
├── FastMCP: {app_config.fastmcp.transport} with tools {app_config.fastmcp.tools}
├── Resources: max {app_config.resources.max_memory_mb}MB, {app_config.resources.max_connections} connections
├── Logging: {app_config.logging.level} ({app_config.logging.format})
├── Health: {app_config.health.endpoint} every {app_config.health.health_interval}s
└── Secrets: ✓ Loaded
    """


# Global configuration instances
app_config, secrets_config = load_config()
