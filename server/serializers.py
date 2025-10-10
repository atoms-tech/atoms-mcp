"""
Markdown serialization for MCP tool responses.

This module provides utilities to convert Python objects to well-formatted
Markdown for better readability and token efficiency in LLM interactions.

Pythonic Patterns Applied:
- Type hints throughout
- Protocol for extensibility
- Generator expressions for memory efficiency
- Dataclass for configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class SerializerConfig:
    """Configuration for Markdown serialization.
    
    Attributes:
        max_string_length: Maximum length for string values before truncation
        max_list_items: Maximum number of list items to show inline
        indent_size: Number of spaces per indentation level
        show_metadata: Whether to show metadata fields
    """
    max_string_length: int = 100
    max_list_items: int = 3
    indent_size: int = 2
    show_metadata: bool = True
    metadata_fields: tuple[str, ...] = field(
        default_factory=lambda: ("count", "total_results", "search_time_ms", "timestamp")
    )


class Serializable(Protocol):
    """Protocol for objects that can be serialized to Markdown."""

    def to_markdown(self) -> str:
        """Convert object to Markdown representation."""
        ...


def serialize_to_markdown(
    data: Any,
    config: SerializerConfig | None = None
) -> str:
    """Serialize tool responses as Markdown for better readability.
    
    Converts Python objects to well-formatted Markdown:
    - Dicts → Tables or code blocks
    - Lists → Bulleted or numbered lists
    - Primitives → Inline code or plain text
    
    Args:
        data: Data to serialize
        config: Optional serializer configuration
        
    Returns:
        Markdown-formatted string
        
    Examples:
        >>> serialize_to_markdown({"success": True, "data": [1, 2, 3]})
        '**Status**: ✅ Success\\n\\n**Results** (3 items):\\n...'
        
        >>> serialize_to_markdown(None)
        '*No data*'
    """
    if config is None:
        config = SerializerConfig()

    if data is None:
        return "*No data*"

    if isinstance(data, str):
        return data  # Already a string, bypass serialization

    if isinstance(data, bool):
        return "✅ Yes" if data else "❌ No"

    if isinstance(data, (int, float)):
        return f"`{data}`"

    if isinstance(data, dict):
        return _dict_to_markdown(data, config=config)

    if isinstance(data, list):
        return _list_to_markdown(data, config=config)

    # Check if object implements Serializable protocol
    if hasattr(data, "to_markdown") and callable(data.to_markdown):
        return data.to_markdown()

    # Fallback to string representation
    return f"```\n{data!s}\n```"


def _dict_to_markdown(
    d: dict[str, Any],
    indent: int = 0,
    config: SerializerConfig | None = None
) -> str:
    """Convert dict to Markdown format.
    
    Args:
        d: Dictionary to convert
        indent: Current indentation level
        config: Serializer configuration
        
    Returns:
        Markdown-formatted string
    """
    if config is None:
        config = SerializerConfig()

    if not d:
        return "*Empty*"

    # Check if dict looks like a single result with success/data structure
    if "success" in d and "data" in d:
        return _format_result_dict(d, config)

    # Regular dict - format as key-value list
    return _format_regular_dict(d, indent, config)


def _format_result_dict(d: dict[str, Any], config: SerializerConfig) -> str:
    """Format a result dictionary with success/data structure.
    
    Args:
        d: Result dictionary
        config: Serializer configuration
        
    Returns:
        Markdown-formatted string
    """
    lines: list[str] = []
    success = d.get("success")
    lines.append(f"**Status**: {'✅ Success' if success else '❌ Failed'}")

    if not success and "error" in d:
        lines.append(f"**Error**: `{d['error']}`")

    if "data" in d:
        data = d["data"]
        if isinstance(data, list) and len(data) > 0:
            lines.append(f"\n**Results** ({len(data)} items):\n")
            lines.append(_list_to_markdown(data, config=config))
        elif isinstance(data, dict):
            lines.append("\n**Data**:")
            lines.append(_dict_to_markdown(data, indent=1, config=config))
        elif data:
            lines.append(f"**Data**: {data}")

    # Add metadata if present and enabled
    if config.show_metadata:
        metadata = {k: v for k, v in d.items() if k in config.metadata_fields}
        if metadata:
            lines.append("\n**Metadata**:")
            lines.extend(f"- {key}: `{value}`" for key, value in metadata.items())

    return "\n".join(lines)


def _format_regular_dict(
    d: dict[str, Any],
    indent: int,
    config: SerializerConfig
) -> str:
    """Format a regular dictionary as key-value list.
    
    Args:
        d: Dictionary to format
        indent: Current indentation level
        config: Serializer configuration
        
    Returns:
        Markdown-formatted string
    """
    lines: list[str] = []
    prefix = " " * (indent * config.indent_size)

    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}**{key}**:")
            lines.append(_dict_to_markdown(value, indent + 1, config))
        elif isinstance(value, list):
            lines.append(f"{prefix}**{key}**: ({len(value)} items)")
            if len(value) <= config.max_list_items:
                lines.append(_list_to_markdown(value, indent + 1, config))
        elif value is None:
            continue  # Skip null values
        else:
            # Truncate long strings
            str_value = str(value)
            if len(str_value) > config.max_string_length:
                str_value = str_value[:config.max_string_length] + "..."
            lines.append(f"{prefix}**{key}**: `{str_value}`")

    return "\n".join(lines)


def _list_to_markdown(
    lst: list[Any],
    indent: int = 0,
    config: SerializerConfig | None = None
) -> str:
    """Convert list to Markdown format.
    
    Args:
        lst: List to convert
        indent: Current indentation level
        config: Serializer configuration
        
    Returns:
        Markdown-formatted string
    """
    if config is None:
        config = SerializerConfig()

    if not lst:
        return "*Empty list*"

    lines: list[str] = []
    prefix = " " * (indent * config.indent_size)

    # If list of dicts (common for entity results), format as cards
    if all(isinstance(item, dict) for item in lst):
        for i, item in enumerate(lst, 1):
            item_name = item.get("name", item.get("id", "Item"))
            lines.append(f"\n{prefix}### {i}. {item_name}")

            # Show key fields only
            key_fields = ["id", "name", "type", "status", "created_at", "similarity_score"]
            for key in key_fields:
                if key in item and item[key] is not None:
                    lines.append(f"{prefix}- **{key}**: `{item[key]}`")
    else:
        # Simple list
        lines.extend(f"{prefix}- {item}" for item in lst)

    return "\n".join(lines)


# Convenience alias for backward compatibility
markdown_serializer = serialize_to_markdown


__all__ = [
    "Serializable",
    "SerializerConfig",
    "markdown_serializer",
    "serialize_to_markdown",
]

