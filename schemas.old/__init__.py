"""
Schemas convenience package.

This module re-exports:
1. Generated models/enums from `schemas.generated.fastapi.schema_public_latest`
2. Application-level constants/enums
3. RLS validators and trigger emulators

The generated exports are built dynamically so new tables/enums automatically
become available without hand-editing this file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from schemas.generated.fastapi import schema_public_latest as generated_schema

if TYPE_CHECKING:
    from collections.abc import Iterable


GeneratedNames = list[str]


def _unique(seq: Iterable[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    ordered: list[str] = []
    for item in seq:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _list_generated_entities() -> GeneratedNames:
    """Extract all entity class names from generated schema."""
    generated_classes = set()
    for name in dir(generated_schema):
        # Only include actual entity classes, not special types
        obj = getattr(generated_schema, name)
        if isinstance(obj, type) and not name.startswith("_"):
            generated_classes.add(name)
    return _unique(sorted(generated_classes))


def __getattr__(name: str):
    """Lazy import generated schema classes."""
    if name.startswith("__"):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    # Allow access to generated schema via attributes
    if hasattr(generated_schema, name):
        return getattr(generated_schema, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Show available attributes including generated schema classes."""
    base_dir = [
        "__doc__",
        "__file__",
        "__getattr__",
        "__name__",
        "__package__",
        "__getattr__",
    ]

    generated_dirs = [attr for attr in dir(generated_schema) if not attr.startswith("_")]

    return sorted(base_dir + generated_dirs)


# Export all generated names
__all__ = []
