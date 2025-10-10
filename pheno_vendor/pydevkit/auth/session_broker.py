"""
OAuth session broker for managing authentication flows.

Provides a simple OAuth token management system without external dependencies.
"""

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class OAuthTokens:
    """OAuth token container."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[float] = None

    def __post_init__(self):
        """Calculate expiration time if not set."""
        if self.expires_at is None and self.expires_in is not None:
            self.expires_at = time.time() + self.expires_in

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if token is expired.

        Args:
            buffer_seconds: Consider token expired this many seconds early

        Returns:
            True if token is expired or will expire within buffer
        """
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthTokens":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class SessionOAuthBroker:
    """
    OAuth session broker for managing authentication flows.

    Simple OAuth token management without external dependencies.
    For production use, consider using authlib or similar libraries.

    Example:
        broker = SessionOAuthBroker(
            client_id="your-client-id",
            token_endpoint="https://oauth.example.com/token"
        )

        # Get tokens
        tokens = broker.exchange_code_for_tokens(auth_code)

        # Refresh tokens
        new_tokens = broker.refresh_tokens(tokens.refresh_token)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        refresh_callback: Optional[Callable[[str], OAuthTokens]] = None,
    ):
        """
        Initialize OAuth broker.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret (optional for public clients)
            token_endpoint: Token endpoint URL
            refresh_callback: Custom callback for token refresh
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.refresh_callback = refresh_callback
        self._current_tokens: Optional[OAuthTokens] = None

    def set_tokens(self, tokens: OAuthTokens) -> None:
        """
        Set current tokens.

        Args:
            tokens: OAuth tokens to store
        """
        self._current_tokens = tokens

    def get_tokens(self) -> Optional[OAuthTokens]:
        """
        Get current tokens.

        Returns:
            Current OAuth tokens or None
        """
        return self._current_tokens

    def get_access_token(self, auto_refresh: bool = True) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary.

        Args:
            auto_refresh: Automatically refresh if expired

        Returns:
            Valid access token or None
        """
        if self._current_tokens is None:
            return None

        if auto_refresh and self._current_tokens.is_expired():
            if self._current_tokens.refresh_token:
                try:
                    self.refresh_tokens(self._current_tokens.refresh_token)
                except Exception:
                    return None

        return self._current_tokens.access_token if self._current_tokens else None

    def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
        code_verifier: Optional[str] = None,
    ) -> OAuthTokens:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code
            redirect_uri: Redirect URI used in authorization
            code_verifier: PKCE code verifier

        Returns:
            OAuth tokens

        Raises:
            NotImplementedError: Requires HTTP client implementation
        """
        raise NotImplementedError(
            "Token exchange requires HTTP client. "
            "Use pydevkit.http.HTTPClient or implement custom exchange."
        )

    def refresh_tokens(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New OAuth tokens

        Raises:
            NotImplementedError: Requires HTTP client implementation or custom callback
        """
        if self.refresh_callback:
            new_tokens = self.refresh_callback(refresh_token)
            self._current_tokens = new_tokens
            return new_tokens

        raise NotImplementedError(
            "Token refresh requires HTTP client or custom callback. "
            "Provide refresh_callback parameter or implement custom refresh."
        )

    def revoke_tokens(self) -> None:
        """Revoke and clear current tokens."""
        self._current_tokens = None

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with valid tokens.

        Returns:
            True if authenticated with valid tokens
        """
        if self._current_tokens is None:
            return False
        return not self._current_tokens.is_expired()


def create_auth_header(token: str, token_type: str = "Bearer") -> Dict[str, str]:
    """
    Create authorization header from token.

    Args:
        token: Access token
        token_type: Token type (default: Bearer)

    Returns:
        Authorization header dict

    Example:
        headers = create_auth_header("abc123")
        # {'Authorization': 'Bearer abc123'}
    """
    return {"Authorization": f"{token_type} {token}"}


__all__ = ["OAuthTokens", "SessionOAuthBroker", "create_auth_header"]
