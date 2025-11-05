"""Atoms MCP logging - direct import from mcp-qa."""

from typing import Any

# Direct import from mcp-qa (from pheno-sdk)
try:
    from pheno.testing.mcp_qa.logging import LogConfig, get_logger
    from pheno.testing.mcp_qa.logging import configure_logging as _configure_logging

    # Backward-compatible wrapper
    def setup_logging(level: str = "INFO", use_color: bool = True, use_timestamps: bool = True, **kwargs):
        """Setup logging with backward-compatible interface."""
        overrides = dict(kwargs)
        fmt_value = overrides.pop("fmt", "plain")
        config_kwargs = {
            "level": level.upper(),
            "color": use_color,
            "timestamp": use_timestamps,
            "fmt": fmt_value,
        }
        allowed_fields = getattr(LogConfig, "__dataclass_fields__", {})
        for extra_key, extra_value in overrides.items():
            if extra_key in allowed_fields:
                config_kwargs[extra_key] = extra_value

        config = LogConfig(**config_kwargs)
        _configure_logging(config)

    def configure_logging(config: Any = None, level: str = "INFO", **kwargs: Any) -> None:
        """Configure logging - accepts either LogConfig or keyword arguments."""
        if config is not None:
            # New style: LogConfig object
            _configure_logging(config)
        else:
            # Old style: keyword arguments
            setup_logging(level=level, **kwargs)

except ImportError:
    import logging

    def configure_logging(config: Any = None, level: str = "INFO", **kwargs: Any) -> None:
        """Fallback logging configuration."""
        target_level = level
        if config is not None and hasattr(config, "level"):
            target_level = config.level

        format_string = kwargs.get("format", "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        logging.basicConfig(
            level=getattr(logging, str(target_level).upper()), format=format_string, datefmt=kwargs.get("datefmt")
        )

    def setup_logging(level: str = "INFO", use_color: bool = True, use_timestamps: bool = True, **kwargs):
        """Fallback setup_logging."""
        components = []
        if use_timestamps:
            components.append("%(asctime)s")

        level_component = "%(levelname)-8s"
        if use_color:
            level_component = "\033[1m%(levelname)-8s\033[0m"
        components.extend([level_component, "%(name)s", "%(message)s"])
        log_format = " | ".join(components)

        configure_logging(level=level, format=log_format, **kwargs)

    get_logger = logging.getLogger  # type: ignore[assignment]

__all__ = ["configure_logging", "get_logger", "setup_logging"]
