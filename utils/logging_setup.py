"""Atoms MCP logging - direct import from mcp-qa."""

# Direct import from mcp-qa (vendored in pheno_vendor)
try:
    from mcp_qa.logging import configure_logging, get_logger

    # Backward-compatible alias
    def setup_logging(level: str = "INFO", **kwargs):
        configure_logging(level=level)

except ImportError:
    import logging

    def configure_logging(level="INFO", **kwargs):
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    setup_logging = configure_logging
    get_logger = logging.getLogger

__all__ = ["configure_logging", "get_logger", "setup_logging"]
