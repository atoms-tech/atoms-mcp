"""
Authentication and OAuth utilities.

Provides OAuth session management, credential handling, MFA/TOTP support,
and secure token storage.
"""

from .session_broker import SessionOAuthBroker, OAuthTokens, create_auth_header
from .credential_manager import (
    InteractiveCredentialManager,
    ensure_oauth_credentials,
    prompt_for_value,
)
from .playwright_adapter import PlaywrightOAuthAdapter, MockBrowserAdapter
from .mfa_handler import MFAHandler, TOTPHandler, generate_totp_secret
from .token_cache import TokenCache, EncryptedTokenStorage, CachedToken

__all__ = [
    "SessionOAuthBroker",
    "OAuthTokens",
    "create_auth_header",
    "InteractiveCredentialManager",
    "ensure_oauth_credentials",
    "prompt_for_value",
    "PlaywrightOAuthAdapter",
    "MockBrowserAdapter",
    "MFAHandler",
    "TOTPHandler",
    "generate_totp_secret",
    "TokenCache",
    "EncryptedTokenStorage",
    "CachedToken",
]