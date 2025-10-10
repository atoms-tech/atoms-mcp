"""HTTP utilities module for PyDevKit."""

from .client import HTTPClient, Response
from .retries import RetryStrategy, exponential_backoff, with_retries
from .headers import HeaderManager, normalize_headers, add_user_agent
from .auth import BearerAuth, BasicAuth, APIKeyAuth

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
