"""
Sensitive secrets configuration for atoms-mcp.
"""

from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecretsSettings(BaseSettings):
    """Secrets and sensitive configuration for atoms-mcp."""
    
    model_config = SettingsConfigDict(
        env_prefix="ATOMS_",
        env_file=".secrets.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Supabase
    supabase_url: Optional[SecretStr] = Field(
        default=None,
        description="Supabase project URL"
    )
    supabase_anon_key: Optional[SecretStr] = Field(
        default=None,
        description="Supabase anonymous key"
    )
    supabase_service_key: Optional[SecretStr] = Field(
        default=None,
        description="Supabase service role key"
    )
    
    # Database
    database_url: Optional[SecretStr] = Field(
        default=None,
        description="Database connection URL"
    )
    
    # Google AI Platform
    google_ai_project: Optional[str] = Field(
        default=None,
        description="Google Cloud project ID"
    )
    google_ai_credentials: Optional[SecretStr] = Field(
        default=None,
        description="Google AI credentials JSON"
    )
    google_ai_location: Optional[str] = Field(
        default="us-central1",
        description="Google AI location"
    )
    
    # WorkOS
    workos_client_id: Optional[str] = Field(
        default=None,
        description="WorkOS client ID"
    )
    workos_api_key: Optional[SecretStr] = Field(
        default=None,
        description="WorkOS API key"
    )
    workos_webhook_secret: Optional[SecretStr] = Field(
        default=None,
        description="WorkOS webhook secret"
    )
    
    # Authentication
    jwt_secret: Optional[SecretStr] = Field(
        default=None,
        description="JWT signing secret"
    )
    session_secret: Optional[SecretStr] = Field(
        default=None,
        description="Session encryption secret"
    )
    
    # External services
    webhook_secret: Optional[SecretStr] = Field(
        default=None,
        description="Webhook signature secret"
    )
    
    def get_supabase_url(self) -> Optional[str]:
        """Get Supabase URL as plain string."""
        return self.supabase_url.get_secret_value() if self.supabase_url else None
    
    def get_supabase_anon_key(self) -> Optional[str]:
        """Get Supabase anonymous key as plain string."""
        return self.supabase_anon_key.get_secret_value() if self.supabase_anon_key else None
    
    def get_supabase_service_key(self) -> Optional[str]:
        """Get Supabase service key as plain string."""
        return self.supabase_service_key.get_secret_value() if self.supabase_service_key else None
    
    def get_google_credentials(self) -> Optional[str]:
        """Get Google AI credentials as plain string."""
        return self.google_ai_credentials.get_secret_value() if self.google_ai_credentials else None
    
    def get_workos_api_key(self) -> Optional[str]:
        """Get WorkOS API key as plain string."""
        return self.workos_api_key.get_secret_value() if self.workos_api_key else None
    
    def has_supabase_config(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.supabase_url and self.supabase_anon_key)
    
    def has_google_ai_config(self) -> bool:
        """Check if Google AI is properly configured."""
        return bool(self.google_ai_project and self.google_ai_credentials)


# Global instance
_secrets: Optional[SecretsSettings] = None


def get_secrets() -> SecretsSettings:
    """Get the global secrets instance."""
    global _secrets
    if _secrets is None:
        _secrets = SecretsSettings()
    return _secrets


def set_secrets(secrets: SecretsSettings) -> None:
    """Set the global secrets instance."""
    global _secrets
    _secrets = secrets
