"""HTTP utilities module for PyDevKit."""

from .auth import APIKeyAuth, BasicAuth, BearerAuth
from .client import HTTPClient, Response
from .headers import HeaderManager, add_user_agent, normalize_headers
from .retries import RetryStrategy, exponential_backoff, with_retries

__all__ = [
    "HTTPClient",
    "Response",
    "RetryStrategy",
    "exponential_backoff",
    "with_retries",
    "HeaderManager",
    "normalize_headers",
    "add_user_agent",
    "BearerAuth",
    "BasicAuth",
    "APIKeyAuth",
]
