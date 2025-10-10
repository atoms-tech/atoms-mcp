"""Configuration manager with hierarchical loading."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigManager:
    """
    Hierarchical configuration manager.

    Supports loading from multiple sources with priority:
    1. Environment variables (highest priority)
    2. Config files (YAML/JSON)
    3. Default values (lowest priority)

    Example:
        config = ConfigManager()
        config.load_from_file('config.json')
        config.load_from_env(prefix='APP_')

        db_url = config.get('database.url')
        timeout = config.get('api.timeout', default=30)
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration manager.

        Args:
            config_dict: Optional initial configuration dictionary
        """
        self._config: Dict[str, Any] = config_dict or {}
        self._frozen = False

    def load_from_file(self, file_path: Union[str, Path]) -> 'ConfigManager':
        """
        Load configuration from JSON or YAML file.

        Args:
            file_path: Path to configuration file

        Returns:
            Self for chaining
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        if path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        elif path.suffix in {'.yaml', '.yml'}:
            data = self._load_yaml(path)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        self._merge_config(data)
        return self

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file (fallback to JSON-style if PyYAML not available)."""
        try:
            import yaml
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback: try to load as JSON
            with open(path, 'r') as f:
                return json.load(f)

    def load_from_env(self, prefix: str = '', separator: str = '__') -> 'ConfigManager':
        """
        Load configuration from environment variables.

        Environment variables are converted to nested config using separator.

        Example:
            APP__DATABASE__URL=postgresql://... -> config.database.url

        Args:
            prefix: Prefix for environment variables (e.g., 'APP_')
            separator: Separator for nested keys (default: '__')

        Returns:
            Self for chaining
        """
        env_config: Dict[str, Any] = {}

        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue

            # Remove prefix
            config_key = key[len(prefix):] if prefix else key

            # Convert to nested dict
            parts = config_key.lower().split(separator)
            current = env_config

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Try to parse value as JSON, fallback to string
            try:
                current[parts[-1]] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                current[parts[-1]] = value

        self._merge_config(env_config)
        return self

    def load_from_dict(self, config_dict: Dict[str, Any]) -> 'ConfigManager':
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            Self for chaining
        """
        self._merge_config(config_dict)
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'database.url')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        current = self._config

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]

        return current

    def set(self, key: str, value: Any) -> 'ConfigManager':
        """
        Set configuration value by dot-separated key.

        Args:
            key: Dot-separated key (e.g., 'database.url')
            value: Value to set

        Returns:
            Self for chaining
        """
        if self._frozen:
            raise RuntimeError("Configuration is frozen")

        parts = key.split('.')
        current = self._config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value
        return self

    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.

        Args:
            key: Dot-separated key

        Returns:
            True if key exists
        """
        parts = key.split('.')
        current = self._config

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        return True

    def delete(self, key: str) -> 'ConfigManager':
        """
        Delete configuration key.

        Args:
            key: Dot-separated key

        Returns:
            Self for chaining
        """
        if self._frozen:
            raise RuntimeError("Configuration is frozen")

        parts = key.split('.')
        current = self._config

        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return self
            current = current[part]

        current.pop(parts[-1], None)
        return self

    def freeze(self) -> 'ConfigManager':
        """
        Freeze configuration (prevent modifications).

        Returns:
            Self for chaining
        """
        self._frozen = True
        return self

    def unfreeze(self) -> 'ConfigManager':
        """
        Unfreeze configuration (allow modifications).

        Returns:
            Self for chaining
        """
        self._frozen = False
        return self

    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self._config.copy()

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration into existing config."""
        self._config = self._deep_merge(self._config, new_config)

    @staticmethod
    def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def __repr__(self) -> str:
        """String representation."""
        return f"ConfigManager(keys={list(self._config.keys())})"


# Global config instance
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get global configuration instance.

    Returns:
        Global ConfigManager instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


def set_global_config(config: ConfigManager) -> None:
    """
    Set global configuration instance.

    Args:
        config: ConfigManager instance to use as global
    """
    global _global_config
    _global_config = config
