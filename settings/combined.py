"""
Combined settings that unify app and secrets configuration.
"""

from typing import Optional, Dict, Any
from .app import AppSettings, get_app_settings as _get_app_settings
from .secrets import SecretsSettings, get_secrets as _get_secrets


class AtomsSettings:
    """Unified configuration for atoms-mcp."""
    
    def __init__(
        self,
        app: Optional[AppSettings] = None,
        secrets: Optional[SecretsSettings] = None
    ):
        """Initialize with custom app and secrets settings."""
        self._app = app or _get_app_settings()
        self._secrets = secrets or _get_secrets()
    
    @property
    def app(self) -> AppSettings:
        """Access to non-sensitive application settings."""
        return self._app
    
    @property
    def secrets(self) -> SecretsSettings:
        """Access to sensitive secrets."""
        return self._secrets
    
    # Convenience methods
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return {
            "host": self.app.host,
            "port": self.app.port,
            "url": self.app.get_server_url(),
        }
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP server configuration."""
        return {
            "name": self.app.mcp_server_name,
            "server_url": self.app.get_server_url(),
        }
    
    def get_supabase_config(self) -> Optional[Dict[str, str]]:
        """Get Supabase configuration if enabled."""
        if not self.app.enable_supabase or not self.secrets.has_supabase_config():
            return None
        
        config = {}
        if self.secrets.supabase_url:
            config["url"] = self.secrets.get_supabase_url()
        if self.secrets.supabase_anon_key:
            config["anon_key"] = self.secrets.get_supabase_anon_key()
        if self.secrets.supabase_service_key:
            config["service_key"] = self.secrets.get_supabase_service_key()
        
        return config
    
    def get_google_ai_config(self) -> Optional[Dict[str, str]]:
        """Get Google AI configuration if enabled."""
        if not self.app.enable_google_ai or not self.secrets.has_google_ai_config():
            return None
        
        config = {
            "project": self.secrets.google_ai_project,
            "location": self.secrets.google_ai_location,
        }
        
        if self.secrets.google_ai_credentials:
            config["credentials"] = self.secrets.get_google_credentials()
        
        return config
    
    def get_workos_config(self) -> Optional[Dict[str, str]]:
        """Get WorkOS configuration if enabled."""
        if not self.app.enable_workos:
            return None
        
        config = {}
        if self.secrets.workos_client_id:
            config["client_id"] = self.secrets.workos_client_id
        if self.secrets.workos_api_key:
            config["api_key"] = self.secrets.get_workos_api_key()
        if self.secrets.workos_webhook_secret:
            config["webhook_secret"] = self.secrets.workos_webhook_secret.get_secret_value()
        
        return config
    
    def get_database_config(self) -> str:
        """Get database URL."""
        if self.secrets.database_url:
            return self.secrets.database_url.get_secret_value()
        return "sqlite://atoms.db"  # Default SQLite
    
    def get_workspace_config(self) -> Dict[str, str]:
        """Get workspace configuration."""
        return {
            "root": self.app.get_workspace_path(),
        }
    
    def is_configured(self) -> bool:
        """Check if any major integration is properly configured."""
        return any([
            self.secrets.has_supabase_config(),
            self.secrets.has_google_ai_config(),
            self.secrets.workos_api_key is not None,
        ])
    
    def to_dict_safe(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary without exposing secrets.
        
        Returns:
            Dictionary with safe values only.
        """
        return {
            "app": self.app.model_dump(),
            "has_secrets": {
                "supabase": self.secrets.has_supabase_config(),
                "google_ai": self.secrets.has_google_ai_config(),
                "workos": self.secrets.workos_api_key is not None,
                "database": bool(self.secrets.database_url),
                "jwt": bool(self.secrets.jwt_secret),
                "session": bool(self.secrets.session_secret),
            },
            "features": {
                "fastapi": self.app.enable_fastapi,
                "supabase": self.app.enable_supabase,
                "google_ai": self.app.enable_google_ai,
                "workos": self.app.enable_workos,
            }
        }


# Global instance
_settings: Optional[AtomsSettings] = None


def get_settings() -> AtomsSettings:
    """Get the global unified settings instance."""
    global _settings
    if _settings is None:
        _settings = AtomsSettings()
    return _settings


def set_settings(settings: AtomsSettings) -> None:
    """Set the global unified settings instance."""
    global _settings
    _settings = settings


def reload_settings() -> AtomsSettings:
    """Reload settings from environment variables."""
    global _settings
    _settings = AtomsSettings(
        app=AppSettings(),
        secrets=SecretsSettings()
    )
    return _settings
