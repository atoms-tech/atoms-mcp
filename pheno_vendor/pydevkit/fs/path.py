"""Path handling utilities."""

from pathlib import Path
from typing import Union


def safe_join(base: Union[str, Path], *paths: str) -> str:
    """
    Safely join paths, preventing directory traversal.

    Example:
        safe_join("/base", "file.txt")  # OK
        safe_join("/base", "../etc/passwd")  # Raises ValueError
    """
    base_path = Path(base).resolve()
    result = base_path.joinpath(*paths).resolve()

    # Ensure result is within base
    try:
        result.relative_to(base_path)
    except ValueError:
        raise ValueError(f"Path traversal detected: {result}")

    return str(result)


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_extension(filename: str) -> str:
    """Get file extension."""
    return Path(filename).suffix


def change_extension(filename: str, new_ext: str) -> str:
    """Change file extension."""
    p = Path(filename)
    if not new_ext.startswith('.'):
        new_ext = f'.{new_ext}'
    return str(p.with_suffix(new_ext))
