"""Atoms MCP logging - direct import from mcp-qa."""

# Direct import from mcp-qa (vendored in pheno_vendor)
try:
    from mcp_qa.logging import LogConfig, configure_logging as _configure_logging, get_logger

    # Backward-compatible wrapper
    def setup_logging(level: str = "INFO", use_color: bool = True, use_timestamps: bool = True, **kwargs):
        """Setup logging with backward-compatible interface."""
        config = LogConfig(
            level=level.upper(),
            color=use_color,
            timestamp=use_timestamps,
            fmt="plain"
        )
        _configure_logging(config)

    def configure_logging(config=None, level: str = "INFO", **kwargs):
        """Configure logging - accepts either LogConfig or keyword arguments."""
        if config is not None:
            # New style: LogConfig object
            _configure_logging(config)
        else:
            # Old style: keyword arguments
            setup_logging(level=level, **kwargs)

except ImportError:
    import logging

    def configure_logging(config=None, level="INFO", **kwargs):
        """Fallback logging configuration."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    def setup_logging(level: str = "INFO", use_color: bool = True, use_timestamps: bool = True, **kwargs):
        """Fallback setup_logging."""
        configure_logging(level=level)

    get_logger = logging.getLogger

__all__ = ["configure_logging", "get_logger", "setup_logging"]
