"""Atoms MCP configuration package."""

from __future__ import annotations

from typing import Tuple

from . import settings as _settings

__all__ = [
    "app_config",
    "get_config_summary",
    "get_settings",
    "load_config",
    "reset_settings_cache",
    "secrets_config",
]


def _sync_settings(app_settings, secret_settings) -> Tuple[object, object]:
    """Keep module-level and settings module globals aligned."""

    _settings.app_config = app_settings
    _settings.secrets_config = secret_settings
    globals()["app_config"] = app_settings
    globals()["secrets_config"] = secret_settings
    return app_settings, secret_settings


def load_config() -> tuple[_settings.AppConfig, _settings.SecretsConfig]:
    """Reload configuration from disk and update exported state."""

    app_settings, secret_settings = _settings.load_config()
    return _sync_settings(app_settings, secret_settings)


def get_config_summary(
    app_settings: _settings.AppConfig,
    secret_settings: _settings.SecretsConfig,
) -> str:
    return _settings.get_config_summary(app_settings, secret_settings)


def get_settings() -> _settings.AppConfig:
    """Legacy helper retained for backwards compatibility."""

    return globals()["app_config"]


def reset_settings_cache() -> None:
    """Backward-compatible cache reset; forces reload from YAML files."""

    load_config()


# Initialize module-level exports
app_config, secrets_config = _sync_settings(
    _settings.app_config, _settings.secrets_config
)
