__all__ = ["create_consolidated_server", "main"]

# Only import if running as package, not during testing
try:
    from .server import create_consolidated_server, main  # noqa: F401
except ImportError:
    # Running in test mode or standalone
    pass

