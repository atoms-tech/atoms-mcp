"""HTTP header management utilities."""

import platform
import sys
from typing import Any, Dict, Optional


class HeaderManager:
    """
    Manage HTTP headers with smart defaults.

    Example:
        headers = HeaderManager()
        headers.set('X-API-Key', 'secret')
        headers.add_json_content_type()
        request_headers = headers.to_dict()
    """

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """Initialize header manager with optional initial headers."""
        self._headers: Dict[str, str] = {}
        if headers:
            self._headers.update(headers)

    def set(self, name: str, value: str) -> 'HeaderManager':
        """Set header value."""
        self._headers[name] = value
        return self

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value."""
        return self._headers.get(name, default)

    def delete(self, name: str) -> 'HeaderManager':
        """Remove header."""
        self._headers.pop(name, None)
        return self

    def update(self, headers: Dict[str, str]) -> 'HeaderManager':
        """Update multiple headers."""
        self._headers.update(headers)
        return self

    def to_dict(self) -> Dict[str, str]:
        """Get headers as dictionary."""
        return self._headers.copy()

    def add_json_content_type(self) -> 'HeaderManager':
        """Add JSON content type header."""
        return self.set('Content-Type', 'application/json')

    def add_form_content_type(self) -> 'HeaderManager':
        """Add form content type header."""
        return self.set('Content-Type', 'application/x-www-form-urlencoded')

    def add_user_agent(self, app_name: str = 'PyDevKit', version: str = '0.1.0') -> 'HeaderManager':
        """Add User-Agent header with system information."""
        user_agent = create_user_agent(app_name, version)
        return self.set('User-Agent', user_agent)

    def add_authorization(self, token: str, scheme: str = 'Bearer') -> 'HeaderManager':
        """Add Authorization header."""
        return self.set('Authorization', f'{scheme} {token}')

    def add_api_key(self, api_key: str, header_name: str = 'X-API-Key') -> 'HeaderManager':
        """Add API key header."""
        return self.set(header_name, api_key)

    def add_correlation_id(self, correlation_id: str) -> 'HeaderManager':
        """Add correlation ID for request tracing."""
        return self.set('X-Correlation-ID', correlation_id)

    def add_accept_json(self) -> 'HeaderManager':
        """Add Accept header for JSON responses."""
        return self.set('Accept', 'application/json')


def normalize_headers(headers: Dict[str, Any]) -> Dict[str, str]:
    """
    Normalize header names and values.

    Args:
        headers: Dictionary of headers

    Returns:
        Normalized headers with title-case names and string values
    """
    normalized = {}
    for key, value in headers.items():
        # Normalize key to title case (e.g., 'content-type' -> 'Content-Type')
        normalized_key = '-'.join(word.capitalize() for word in key.split('-'))
        # Convert value to string
        normalized[normalized_key] = str(value)

    return normalized


def add_user_agent(
    headers: Dict[str, str],
    app_name: str = 'PyDevKit',
    version: str = '0.1.0',
) -> Dict[str, str]:
    """
    Add User-Agent header to existing headers.

    Args:
        headers: Existing headers dictionary
        app_name: Application name
        version: Application version

    Returns:
        Headers with User-Agent added
    """
    headers = headers.copy()
    headers['User-Agent'] = create_user_agent(app_name, version)
    return headers


def create_user_agent(app_name: str = 'PyDevKit', version: str = '0.1.0') -> str:
    """
    Create comprehensive User-Agent string.

    Args:
        app_name: Application name
        version: Application version

    Returns:
        User-Agent string with system information

    Example:
        'MyApp/1.0.0 (Python/3.11.0; Darwin/23.0.0)'
    """
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    system = platform.system()
    system_version = platform.release()

    return f"{app_name}/{version} (Python/{python_version}; {system}/{system_version})"


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Extract bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Extracted token or None if not found
    """
    if not authorization:
        return None

    parts = authorization.split(' ', 1)
    if len(parts) != 2:
        return None

    scheme, token = parts
    if scheme.lower() != 'bearer':
        return None

    return token


def extract_basic_auth(authorization: Optional[str]) -> Optional[tuple[str, str]]:
    """
    Extract username and password from Basic Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Tuple of (username, password) or None if invalid
    """
    import base64

    if not authorization:
        return None

    parts = authorization.split(' ', 1)
    if len(parts) != 2:
        return None

    scheme, credentials = parts
    if scheme.lower() != 'basic':
        return None

    try:
        decoded = base64.b64decode(credentials).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username, password
    except Exception:
        return None


def build_cache_control(
    max_age: Optional[int] = None,
    no_cache: bool = False,
    no_store: bool = False,
    public: bool = False,
    private: bool = False,
) -> str:
    """
    Build Cache-Control header value.

    Args:
        max_age: Maximum age in seconds
        no_cache: Disable caching
        no_store: Prevent storage
        public: Allow public caching
        private: Allow only private caching

    Returns:
        Cache-Control header value
    """
    directives = []

    if no_cache:
        directives.append('no-cache')
    if no_store:
        directives.append('no-store')
    if public:
        directives.append('public')
    if private:
        directives.append('private')
    if max_age is not None:
        directives.append(f'max-age={max_age}')

    return ', '.join(directives) if directives else 'no-cache'
