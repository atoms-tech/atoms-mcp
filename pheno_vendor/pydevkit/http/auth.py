"""HTTP authentication helpers."""

import base64
from typing import Dict, Optional, Protocol


class AuthProvider(Protocol):
    """Protocol for authentication providers."""

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        ...


class BearerAuth:
    """
    Bearer token authentication.

    Example:
        auth = BearerAuth('my-token')
        headers = auth.get_headers()
        # {'Authorization': 'Bearer my-token'}
    """

    def __init__(self, token: str):
        """
        Initialize bearer auth.

        Args:
            token: Bearer token
        """
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """Get authorization header."""
        return {'Authorization': f'Bearer {self.token}'}


class BasicAuth:
    """
    HTTP Basic authentication.

    Example:
        auth = BasicAuth('username', 'password')
        headers = auth.get_headers()
        # {'Authorization': 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='}
    """

    def __init__(self, username: str, password: str):
        """
        Initialize basic auth.

        Args:
            username: Username
            password: Password
        """
        self.username = username
        self.password = password

    def get_headers(self) -> Dict[str, str]:
        """Get authorization header."""
        credentials = f'{self.username}:{self.password}'
        encoded = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}


class APIKeyAuth:
    """
    API key authentication.

    Example:
        auth = APIKeyAuth('my-api-key')
        headers = auth.get_headers()
        # {'X-API-Key': 'my-api-key'}

        # Custom header name
        auth = APIKeyAuth('my-key', header_name='X-Custom-Key')
    """

    def __init__(self, api_key: str, header_name: str = 'X-API-Key'):
        """
        Initialize API key auth.

        Args:
            api_key: API key
            header_name: Header name for API key
        """
        self.api_key = api_key
        self.header_name = header_name

    def get_headers(self) -> Dict[str, str]:
        """Get API key header."""
        return {self.header_name: self.api_key}


class QueryParamAuth:
    """
    Query parameter authentication.

    Example:
        auth = QueryParamAuth('my-api-key', param_name='api_key')
        params = auth.get_params()
        # {'api_key': 'my-api-key'}
    """

    def __init__(self, api_key: str, param_name: str = 'api_key'):
        """
        Initialize query param auth.

        Args:
            api_key: API key
            param_name: Query parameter name
        """
        self.api_key = api_key
        self.param_name = param_name

    def get_params(self) -> Dict[str, str]:
        """Get query parameters."""
        return {self.param_name: self.api_key}

    def get_headers(self) -> Dict[str, str]:
        """Get empty headers (auth is in query params)."""
        return {}


def validate_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Validate and extract bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Extracted token or None if invalid
    """
    if not authorization:
        return None

    parts = authorization.split(' ', 1)
    if len(parts) != 2:
        return None

    scheme, token = parts
    if scheme.lower() != 'bearer':
        return None

    return token if token else None


def validate_basic_auth(authorization: Optional[str]) -> Optional[tuple[str, str]]:
    """
    Validate and extract credentials from Basic Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Tuple of (username, password) or None if invalid
    """
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
        if ':' not in decoded:
            return None
        username, password = decoded.split(':', 1)
        return username, password
    except Exception:
        return None


def has_scope(scopes_str: Optional[str], required_scopes: set[str]) -> bool:
    """
    Check if scopes string contains required scopes.

    Args:
        scopes_str: Space-separated scopes string
        required_scopes: Set of required scopes

    Returns:
        True if all required scopes are present
    """
    if not scopes_str:
        return False

    try:
        scopes = set(scopes_str.split())
        return required_scopes.issubset(scopes)
    except Exception:
        return False


def has_any_scope(scopes_str: Optional[str], allowed_scopes: set[str]) -> bool:
    """
    Check if scopes string contains any of the allowed scopes.

    Args:
        scopes_str: Space-separated scopes string
        allowed_scopes: Set of allowed scopes

    Returns:
        True if any allowed scope is present
    """
    if not scopes_str:
        return False

    try:
        scopes = set(scopes_str.split())
        return bool(scopes & allowed_scopes)
    except Exception:
        return False
