"""
YAML-based configuration management for atoms-mcp-prod.

Uses config.yml for non-sensitive settings and secrets.yml for sensitive data.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class YamlAppSettings(BaseModel):
    """Non-sensitive application settings from config.yml."""
    
    app_name: str = Field(default="atoms-mcp-prod", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    server_host: str = Field(default="localhost", description="Server host")
    server_port: int = Field(default=8000, description="Server port")
    server_workers: int = Field(default=1, description="Worker processes")
    server_timeout: int = Field(default=30, description="Request timeout")
    
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="text", description="Log format")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    enable_metrics: bool = Field(default=True, description="Enable metrics")
    enable_telemetry: bool = Field(default=True, description="Enable telemetry")
    enable_debug_mode: bool = Field(default=False, description="Enable debug mode")
    
    cache_ttl: int = Field(default=3600, description="Cache TTL seconds")
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    rate_limit_rpm: int = Field(default=60, description="Rate limit per minute")
    
    @validator('server_port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        extra = "ignore"


class YamlSecrets(BaseModel):
    """Sensitive settings from secrets.yml."""
    
    api_keys_openrouter: Optional[str] = Field(default=None, description="OpenRouter API key")
    api_keys_anthropic: Optional[str] = Field(default=None, description="Anthropic API key")
    api_keys_openai: Optional[str] = Field(default=None, description="OpenAI API key")
    api_keys_google_ai: Optional[str] = Field(default=None, description="Google AI API key")
    
    database_url: Optional[str] = Field(default=None, description="Database URL")
    redis_url: Optional[str] = Field(default=None, description="Redis URL")
    
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret")
    session_secret: Optional[str] = Field(default=None, description="Session secret")
    oauth_client_secret: Optional[str] = Field(default=None, description="OAuth client secret")
    
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret")
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    datadog_api_key: Optional[str] = Field(default=None, description="Datadog API key")
    langsmith_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    
    supabase_url: Optional[str] = Field(default=None, description="Supabase URL")
    supabase_anon_key: Optional[str] = Field(default=None, description="Supabase anon key")
    supabase_service_key: Optional[str] = Field(default=None, description="Supabase service key")
    workos_api_key: Optional[str] = Field(default=None, description="WorkOS API key")
    google_cloud_credentials: Optional[str] = Field(default=None, description="Google Cloud credentials")
    
    class Config:
        extra = "ignore"
    
    def has_any_api_key(self) -> bool:
        """Check if any API key is configured."""
        return any([
            self.api_keys_openrouter,
            self.api_keys_anthropic,
            self.api_keys_openai,
            self.api_keys_google_ai,
        ])


class YamlSettings:
    """Unified YAML configuration."""
    
    def __init__(self, config_path: Optional[Path] = None, secrets_path: Optional[Path] = None):
        self.project_root = Path.cwd()
        self.config_path = config_path or (self.project_root / "config.yml")
        self.secrets_path = secrets_path or (self.project_root / "secrets.yml")
        
        self._app = self._load_config()
        self._secrets = self._load_secrets()
    
    def _load_config(self) -> YamlAppSettings:
        """Load configuration from config.yml."""
        if not self.config_path.exists():
            print(f"⚠️  config.yml not found at {self.config_path}, using defaults")
            return YamlAppSettings()
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Flatten nested structure
            flat_data = {}
            flat_data.update(data.get('app', {}))
            flat_data.update(data.get('server', {}))
            flat_data.update(data.get('logging', {}))
            flat_data.update(data.get('features', {}))
            flat_data.update(data.get('performance', {}))
            
            # Map to expected field names
            mapped_data = {
                'app_name': flat_data.get('name'),
                'version': flat_data.get('version'),
                'environment': flat_data.get('environment'),
                'debug': flat_data.get('debug'),
                'server_host': flat_data.get('host'),
                'server_port': flat_data.get('port'),
                'server_workers': flat_data.get('workers'),
                'server_timeout': flat_data.get('timeout'),
                'log_level': flat_data.get('level'),
                'log_format': flat_data.get('format'),
                'log_file': flat_data.get('file'),
                'enable_metrics': flat_data.get('enable_metrics'),
                'enable_telemetry': flat_data.get('enable_telemetry'),
                'enable_debug_mode': flat_data.get('enable_debug_mode'),
                'cache_ttl': flat_data.get('cache_ttl'),
                'max_concurrent_requests': flat_data.get('max_concurrent_requests'),
                'rate_limit_rpm': flat_data.get('rate_limit_rpm'),
            }
            
            return YamlAppSettings(**{k: v for k, v in mapped_data.items() if v is not None})
            
        except Exception as e:
            print(f"❌ Error loading config.yml: {e}")
            return YamlAppSettings()
    
    def _load_secrets(self) -> YamlSecrets:
        """Load secrets from secrets.yml."""
        if not self.secrets_path.exists():
            print(f"⚠️  secrets.yml not found at {self.secrets_path}, using defaults")
            return YamlSecrets()
        
        try:
            with open(self.secrets_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            secrets_data = data.get('secrets', {})
            flat_data = {}
            
            # Flatten nested structure
            for category, values in secrets_data.items():
                if isinstance(values, dict):
                    for key, value in values.items():
                        flat_key = f"{category}_{key}"
                        flat_data[flat_key] = value
                else:
                    flat_data[category] = values
            
            # Map to expected field names
            mapped_data = {
                'api_keys_openrouter': flat_data.get('api_keys_openrouter'),
                'api_keys_anthropic': flat_data.get('api_keys_anthropic'),
                'api_keys_openai': flat_data.get('api_keys_openai'),
                'api_keys_google_ai': flat_data.get('api_keys_google_ai'),
                'database_url': flat_data.get('database_url'),
                'redis_url': flat_data.get('redis_url'),
                'jwt_secret': flat_data.get('authentication_jwt_secret'),
                'session_secret': flat_data.get('authentication_session_secret'),
                'oauth_client_secret': flat_data.get('authentication_oauth_client_secret'),
                'webhook_secret': flat_data.get('external_services_webhook_secret'),
                'sentry_dsn': flat_data.get('external_services_sentry_dsn'),
                'datadog_api_key': flat_data.get('external_services_datadog_api_key'),
                'langsmith_api_key': flat_data.get('external_services_langsmith_api_key'),
                'supabase_url': flat_data.get('third_party_supabase_url'),
                'supabase_anon_key': flat_data.get('third_party_supabase_anon_key'),
                'supabase_service_key': flat_data.get('third_party_supabase_service_key'),
                'workos_api_key': flat_data.get('third_party_workos_api_key'),
                'google_cloud_credentials': flat_data.get('third_party_google_cloud_credentials'),
            }
            
            return YamlSecrets(**{k: v for k, v in mapped_data.items() if v is not None})
            
        except Exception as e:
            print(f"❌ Error loading secrets.yml: {e}")
            return YamlSecrets()
    
    @property
    def app(self) -> YamlAppSettings:
        """Access to app settings."""
        return self._app
    
    @property
    def secrets(self) -> YamlSecrets:
        """Access to secrets."""
        return self._secrets
    
    def is_configured(self) -> bool:
        """Check if essential configuration is present."""
        return self.secrets.has_any_api_key()
    
    def get_server_url(self) -> str:
        """Get full server URL."""
        return f"http://{self.app.server_host}:{self.app.server_port}"
    
    def to_dict_safe(self) -> Dict[str, Any]:
        """Convert to dictionary without exposing secrets."""
        return {
            "app": self.app.dict(),
            "has_secrets": {
                "openrouter": bool(self.secrets.api_keys_openrouter),
                "anthropic": bool(self.secrets.api_keys_anthropic),
                "openai": bool(self.secrets.api_keys_openai),
                "google_ai": bool(self.secrets.api_keys_google_ai),
                "database": bool(self.secrets.database_url),
                "redis": bool(self.secrets.redis_url),
                "jwt": bool(self.secrets.jwt_secret),
                "sentry": bool(self.secrets.sentry_dsn),
                "supabase": bool(self.secrets.supabase_url),
            }
        }


# Global instance
_settings: Optional[YamlSettings] = None


def get_settings() -> YamlSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = YamlSettings()
    return _settings


def set_settings(settings: YamlSettings) -> None:
    """Set the global settings instance."""
    global _settings
    _settings = settings


def reload_settings() -> YamlSettings:
    """Reload settings from YAML files."""
    global _settings
    _settings = YamlSettings()
    return _settings


# Backward compatibility aliases
AppSettings = YamlAppSettings
SecretsSettings = YamlSecrets
