"""Environment variable utilities."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Union


T = TypeVar('T')


class EnvLoader:
    """
    Load and parse environment variables.

    Example:
        env = EnvLoader(prefix='APP_')
        db_url = env.get('DATABASE_URL', required=True)
        debug = env.get_bool('DEBUG', default=False)
        port = env.get_int('PORT', default=8000)
    """

    def __init__(self, prefix: str = ''):
        """
        Initialize environment loader.

        Args:
            prefix: Prefix for environment variable names
        """
        self.prefix = prefix

    def _get_key(self, name: str) -> str:
        """Get full environment variable key with prefix."""
        return f"{self.prefix}{name}"

    def get(self, name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """
        Get environment variable as string.

        Args:
            name: Variable name (without prefix)
            default: Default value if not found
            required: Raise error if not found

        Returns:
            Variable value or default

        Raises:
            ValueError: If required and not found
        """
        key = self._get_key(name)
        value = os.getenv(key, default)

        if required and value is None:
            raise ValueError(f"Required environment variable not found: {key}")

        return value

    def get_int(self, name: str, default: Optional[int] = None, required: bool = False) -> Optional[int]:
        """
        Get environment variable as integer.

        Args:
            name: Variable name (without prefix)
            default: Default value if not found
            required: Raise error if not found

        Returns:
            Integer value or default
        """
        value = self.get(name, required=required)

        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Invalid integer value for {self._get_key(name)}: {value}")

    def get_float(self, name: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
        """Get environment variable as float."""
        value = self.get(name, required=required)

        if value is None:
            return default

        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid float value for {self._get_key(name)}: {value}")

    def get_bool(self, name: str, default: bool = False, required: bool = False) -> bool:
        """
        Get environment variable as boolean.

        Recognizes: true/false, yes/no, 1/0, on/off (case-insensitive)

        Args:
            name: Variable name (without prefix)
            default: Default value if not found
            required: Raise error if not found

        Returns:
            Boolean value
        """
        value = self.get(name, required=required)

        if value is None:
            return default

        value_lower = value.lower().strip()
        if value_lower in {'true', 'yes', '1', 'on'}:
            return True
        elif value_lower in {'false', 'no', '0', 'off', ''}:
            return False
        else:
            raise ValueError(f"Invalid boolean value for {self._get_key(name)}: {value}")

    def get_list(
        self,
        name: str,
        separator: str = ',',
        default: Optional[list[str]] = None,
        required: bool = False
    ) -> list[str]:
        """
        Get environment variable as list of strings.

        Args:
            name: Variable name (without prefix)
            separator: List item separator (default: ',')
            default: Default value if not found
            required: Raise error if not found

        Returns:
            List of strings
        """
        value = self.get(name, required=required)

        if value is None:
            return default or []

        return [item.strip() for item in value.split(separator) if item.strip()]

    def get_dict(
        self,
        name: str,
        item_separator: str = ',',
        key_separator: str = '=',
        default: Optional[Dict[str, str]] = None,
        required: bool = False
    ) -> Dict[str, str]:
        """
        Get environment variable as dictionary.

        Example: "KEY1=val1,KEY2=val2" -> {"KEY1": "val1", "KEY2": "val2"}

        Args:
            name: Variable name (without prefix)
            item_separator: Separator between key-value pairs
            key_separator: Separator between key and value
            default: Default value if not found
            required: Raise error if not found

        Returns:
            Dictionary
        """
        value = self.get(name, required=required)

        if value is None:
            return default or {}

        result = {}
        for item in value.split(item_separator):
            item = item.strip()
            if not item:
                continue

            if key_separator not in item:
                raise ValueError(f"Invalid dict format for {self._get_key(name)}: {item}")

            key, val = item.split(key_separator, 1)
            result[key.strip()] = val.strip()

        return result


def load_env_file(file_path: Union[str, Path], override: bool = True) -> Dict[str, str]:
    """
    Load environment variables from .env file.

    Args:
        file_path: Path to .env file
        override: Whether to override existing environment variables

    Returns:
        Dictionary of loaded variables
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f".env file not found: {file_path}")

    loaded = {}

    with open(path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes from value
            if value and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]

            # Set environment variable
            if override or key not in os.environ:
                os.environ[key] = value
                loaded[key] = value

    return loaded


def get_env(
    name: str,
    default: Optional[T] = None,
    cast: Optional[type] = None,
    required: bool = False
) -> Union[str, T, None]:
    """
    Get environment variable with optional type casting.

    Args:
        name: Environment variable name
        default: Default value if not found
        cast: Type to cast value to (int, float, bool, etc.)
        required: Raise error if not found

    Returns:
        Environment variable value

    Example:
        port = get_env('PORT', default=8000, cast=int)
        debug = get_env('DEBUG', default=False, cast=bool)
    """
    value = os.getenv(name)

    if value is None:
        if required:
            raise ValueError(f"Required environment variable not found: {name}")
        return default

    if cast is None:
        return value

    # Handle boolean casting
    if cast is bool:
        value_lower = value.lower().strip()
        if value_lower in {'true', 'yes', '1', 'on'}:
            return True
        elif value_lower in {'false', 'no', '0', 'off', ''}:
            return False
        else:
            raise ValueError(f"Invalid boolean value for {name}: {value}")

    # Cast to requested type
    try:
        return cast(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to cast {name} to {cast.__name__}: {e}")


def ensure_env(*names: str) -> None:
    """
    Ensure required environment variables are set.

    Args:
        *names: Environment variable names to check

    Raises:
        ValueError: If any required variable is missing
    """
    missing = [name for name in names if name not in os.environ]

    if missing:
        raise ValueError(f"Required environment variables not set: {', '.join(missing)}")
