"""
Authentication and OAuth utilities.

Provides OAuth session management, credential handling, MFA/TOTP support,
and secure token storage.
"""

from .credential_manager import (
    InteractiveCredentialManager,
    ensure_oauth_credentials,
    prompt_for_value,
)
from .mfa_handler import MFAHandler, TOTPHandler, generate_totp_secret
from .playwright_adapter import MockBrowserAdapter, PlaywrightOAuthAdapter
from .session_broker import OAuthTokens, SessionOAuthBroker, create_auth_header
from .token_cache import CachedToken, EncryptedTokenStorage, TokenCache

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
