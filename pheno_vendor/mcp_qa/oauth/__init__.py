"""
Unified OAuth Library for MCP Test Suites

This library provides unified OAuth and credential management by combining
the best features from both Zen MCP Server and atoms_mcp-old implementations.

Key Features:
- Interactive credential prompting with auto .env updates
- Playwright OAuth automation with retry logic
- Session-scoped token caching (encrypted)
- Inline progress display (single overwritten line)
- MFA/TOTP automation support
- Token capture for direct HTTP calls

Quick Start:
    from mcp_qa.oauth import get_credential_broker, ensure_oauth_credentials
    
    # Ensure credentials are available
    creds = await ensure_oauth_credentials("authkit", ["email", "password"])
    
    # Or use the broker directly
    broker = get_credential_broker()
    creds = await broker.ensure_credentials("authkit", ["email", "password"])

Advanced Usage:
    from mcp_qa.oauth import (
        PlaywrightOAuthAdapter,
        SessionTokenManager,
        InlineProgress,
        OAuthTokens
    )
    
    # Create session manager
    session_mgr = SessionTokenManager()
    
    # Set up OAuth adapter
    adapter = PlaywrightOAuthAdapter(
        email="user@example.com",
        password="password",
        provider="authkit"
    )
    
    # Create OAuth client
    client, auth_task = adapter.create_oauth_client("https://mcp.example.com")
    
    # Wait for OAuth URL and automate
    oauth_url = await adapter.wait_for_oauth_url()
    success = await adapter.automate_login_with_retry(oauth_url)
"""

# Credential Management
from .credential_broker import (
    UnifiedCredentialBroker,
    CapturedCredentials,
)

# Playwright OAuth Automation
from .playwright_adapter import PlaywrightOAuthAdapter

# Flow Adapters
from .flow_adapters import (
    OAuthFlowAdapter,
    OAuthFlowFactory,
    AuthKitStandardFlow,
    AuthKitStandaloneConnectFlow,
    GoogleOAuthFlow,
    GitHubOAuthFlow,
    CustomOAuthFlow,
    FlowConfig,
    create_oauth_adapter,
)

# Session & Token Management
from .session_manager import (
    OAuthTokens,
    TokenCache,
    SessionTokenManager,
    get_session_manager,
    clear_oauth_cache,
)

# OAuth Cache (FastMCP integration)
from .cache import (
    CachedOAuthClient,
    create_cached_client,
)

# Progress Display
from .progress import (
    InlineProgress,
    OAuthProgressFlow,
    inline_progress,
)

# Retry-aware helpers
from .retry import (
    RetryConfig,
    EnhancedCredentialBroker,
    RetryOAuthAdapter,
    create_retry_oauth_client,
)

__all__ = [
    # Credential Management
    "UnifiedCredentialBroker",
    "CapturedCredentials",

    # Playwright Adapter
    "PlaywrightOAuthAdapter",

    # Session Management
    "OAuthTokens",
    "TokenCache",
    "SessionTokenManager",
    "get_session_manager",
    "clear_oauth_cache",

    # OAuth Cache
    "CachedOAuthClient",
    "create_cached_client",

    # Progress Display
    "InlineProgress",
    "OAuthProgressFlow",
    "inline_progress",

    # Retry helpers
    "RetryConfig",
    "EnhancedCredentialBroker",
    "RetryOAuthAdapter",
    "create_retry_oauth_client",
]

__version__ = "1.0.0"
