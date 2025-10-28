"""
Environment configuration loading for MCP server.

This module provides utilities for loading environment variables from
.env and .env.local files with proper precedence and validation and
keeps the `config.settings` cache in sync so Pydantic settings always
reflect the latest values.

Pythonic Patterns Applied:
- Type hints throughout
- Dataclass for configuration
- Context manager for temporary env changes
- Generator for env file parsing
- Custom exceptions for error handling
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from config import reset_settings_cache
from utils.logging_setup import get_logger

try:  # pragma: no cover - optional dependency
    from dotenv import dotenv_values  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully at runtime
    dotenv_values = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = get_logger("atoms_fastmcp.env")


class EnvLoadError(Exception):
    """Raised when environment loading fails."""


@dataclass
class EnvConfig:
    """Configuration for environment loading.

    Attributes:
        base_dir: Base directory for .env files
        env_files: List of env files to load (in order of precedence)
        override_existing: Whether to override existing env vars
        required_vars: Set of required environment variables
    """
    base_dir: Path = field(default_factory=Path.cwd)
    env_files: tuple[str, ...] = (".env", ".env.local")
    override_existing: bool = False
    required_vars: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        """Validate configuration."""
        if not self.base_dir.exists():
            raise EnvLoadError(f"Base directory does not exist: {self.base_dir}")


def parse_env_file(file_path: Path) -> Iterator[tuple[str, str]]:
    """Parse environment file and yield key-value pairs.

    Args:
        file_path: Path to .env file

    Yields:
        Tuples of (key, value)

    Examples:
        >>> for key, value in parse_env_file(Path(".env")):
        ...     print(f"{key}={value}")
    """
    if not file_path.exists():
        return

    try:
        with file_path.open(encoding="utf-8") as file_handle:
            for line_num, raw_line in enumerate(file_handle, 1):
                # Skip comments and empty lines
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse key=value
                if "=" not in line:
                    logger.warning(
                        f"Invalid line {line_num} in {file_path}: {line}"
                    )
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1]

                if key:
                    yield key, value
    except Exception as exc:
        logger.exception("Error parsing %s", file_path)
        raise EnvLoadError(f"Failed to parse {file_path}: {exc}") from exc


def _load_env_file(file_path: Path, use_dotenv: bool) -> dict[str, str]:
    """Load environment variables from a single file."""
    if use_dotenv and dotenv_values is not None:
        values = dotenv_values(file_path)
        return {k: v for k, v in values.items() if v is not None} if values else {}

    return dict(parse_env_file(file_path))


def load_env_files(config: EnvConfig | None = None) -> dict[str, str]:
    """Load environment variables from .env files.

    Loads variables from .env and .env.local (if available), with
    .env.local taking precedence. Does not override existing environment
    variables by default.

    Args:
        config: Optional environment configuration

    Returns:
        Dictionary of loaded environment variables

    Raises:
        EnvLoadError: If required variables are missing

    Examples:
        >>> loaded = load_env_files()
        >>> print(f"Loaded {len(loaded)} variables")
    """
    if config is None:
        config = EnvConfig()

    use_dotenv = dotenv_values is not None
    if not use_dotenv and any((config.base_dir / f).exists() for f in config.env_files):
        logger.info(
            "python-dotenv not installed; using basic parser. Install python-dotenv for better .env file support."
        )

    merged: dict[str, str] = {}

    # Load each env file in order
    for env_file in config.env_files:
        file_path = config.base_dir / env_file

        if not file_path.exists():
            logger.debug(f"Env file not found: {file_path}")
            continue

        try:
            values = _load_env_file(file_path, use_dotenv)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed loading %s: %s", env_file, exc)
            continue

        merged.update(values)
        logger.info("Loaded %s variables from %s", len(values), env_file)

    # Apply to environment
    applied_count = 0
    for key, value in merged.items():
        if config.override_existing or key not in os.environ:
            os.environ[key] = value
            applied_count += 1

    logger.info(f"Applied {applied_count} environment variables")

    if applied_count:
        reset_settings_cache()

    # Check required variables
    missing = config.required_vars - set(os.environ.keys())
    if missing:
        raise EnvLoadError(
            f"Missing required environment variables: {', '.join(sorted(missing))}"
        )

    return merged


@contextmanager
def temporary_env(**kwargs: str) -> Iterator[None]:
    """Context manager for temporary environment variable changes.

    Args:
        **kwargs: Environment variables to set temporarily

    Yields:
        None

    Examples:
        >>> with temporary_env(DEBUG="true", LOG_LEVEL="debug"):
        ...     # Environment variables are set
        ...     run_tests()
        >>> # Environment variables are restored
    """
    # Save original values
    original = {key: os.environ.get(key) for key in kwargs}

    try:
        # Set temporary values
        for key, value in kwargs.items():
            os.environ[key] = value
        yield
    finally:
        # Restore original values
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def get_env_var(
    key: str,
    default: str | None = None,
    required: bool = False
) -> str | None:
    """Get environment variable with optional default and validation.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether variable is required

    Returns:
        Environment variable value or default

    Raises:
        EnvLoadError: If required variable is missing

    Examples:
        >>> api_key = get_env_var("API_KEY", required=True)
        >>> debug = get_env_var("DEBUG", default="false")
    """
    value = os.environ.get(key, default)

    if required and value is None:
        raise EnvLoadError(f"Required environment variable not set: {key}")

    return value


def get_fastmcp_vars() -> dict[str, str]:
    """Get all FASTMCP-related environment variables.

    Returns:
        Dictionary of FASTMCP environment variables

    Examples:
        >>> vars = get_fastmcp_vars()
        >>> for key, value in vars.items():
        ...     print(f"{key}={value}")
    """
    return {
        k: v for k, v in os.environ.items()
        if "FASTMCP" in k.upper()
    }


__all__ = [
    "EnvConfig",
    "EnvLoadError",
    "get_env_var",
    "get_fastmcp_vars",
    "load_env_files",
    "parse_env_file",
    "temporary_env",
]
