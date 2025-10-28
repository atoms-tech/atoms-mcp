"""
Non-sensitive application settings for atoms-mcp.
"""

from typing import Literal, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Non-sensitive configuration for atoms-mcp."""
    
    model_config = SettingsConfigDict(
        env_prefix="ATOMS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Server configuration
    host: str = Field(
        default="localhost",
        description="Server host"
    )
    port: int = Field(
        default=8080,
        description="Server port"
    )
    
    # MCP configuration
    mcp_server_name: str = Field(
        default="atoms-mcp",
        description="MCP server name"
    )
    
    # Workspace configuration
    workspace_root: str = Field(
        default="~/atoms",
        description="Atoms workspace root directory"
    )
    
    # Feature flags
    enable_fastapi: bool = Field(
        default=True,
        description="Enable FastAPI HTTP server"
    )
    enable_supabase: bool = Field(
        default=True,
        description="Enable Supabase integration"
    )
    enable_google_ai: bool = Field(
        default=True,
        description="Enable Google AI Platform"
    )
    enable_workos: bool = Field(
        default=True,
        description="Enable WorkOS integration"
    )
    
    # Performance settings
    max_concurrent_requests: int = Field(
        default=100,
        description="Maximum concurrent requests"
    )
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    
    # Logging configuration
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Development settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    def get_server_url(self) -> str:
        """Get full server URL."""
        return f"http://{self.host}:{self.port}"
    
    def get_workspace_path(self) -> str:
        """Get expanded workspace path."""
        import os
        return os.path.expanduser(self.workspace_root)


# Global instance
_app_settings: Optional[AppSettings] = None


def get_app_settings() -> AppSettings:
    """Get the global app settings instance."""
    global _app_settings
    if _app_settings is None:
        _app_settings = AppSettings()
    return _app_settings


def set_app_settings(settings: AppSettings) -> None:
    """Set the global app settings instance."""
    global _app_settings
    _app_settings = settings
