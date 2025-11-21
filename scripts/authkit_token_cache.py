#!/usr/bin/env python3
"""OS keychain utilities for caching AuthKit tokens securely.

This module provides cross-platform keychain access for storing and retrieving
AuthKit JWT tokens. Uses the `keyring` library which supports:
- macOS Keychain
- Windows Credential Manager
- Linux Secret Service (libsecret)
"""

import os
import logging
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Keychain service name and username
KEYCHAIN_SERVICE = "atoms-mcp-authkit"
KEYCHAIN_USERNAME = "authkit-access-token"
KEYCHAIN_REFRESH_USERNAME = "authkit-refresh-token"  # If refresh tokens are available

# Token expiration buffer: refresh if token expires within this many seconds
TOKEN_REFRESH_BUFFER_SECONDS = 300  # 5 minutes before expiration


def get_token_from_keychain() -> Optional[str]:
    """Retrieve AuthKit token from OS keychain.
    
    Returns:
        JWT token string if found, None otherwise
    """
    try:
        import keyring
        token = keyring.get_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
        if token:
            # Validate it's a real JWT (basic check)
            if len(token) >= 100 and token.count(".") >= 2:
                logger.info("✅ Retrieved AuthKit token from keychain")
                return token
            else:
                logger.warning("⚠️  Token in keychain doesn't look like a valid JWT, ignoring")
                return None
        return None
    except ImportError:
        logger.debug("keyring not available, cannot read from keychain")
        return None
    except Exception as e:
        logger.warning(f"Failed to read from keychain: {e}")
        return None


def save_token_to_keychain(token: str) -> bool:
    """Save AuthKit token to OS keychain.
    
    Args:
        token: JWT token string to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        import keyring
        # Validate token format before saving
        if not isinstance(token, str) or len(token) < 100 or token.count(".") < 2:
            logger.warning("⚠️  Token doesn't look like a valid JWT, not saving to keychain")
            return False
        
        keyring.set_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME, token)
        logger.info("✅ Saved AuthKit token to OS keychain")
        return True
    except ImportError:
        logger.debug("keyring not available, cannot save to keychain")
        return False
    except Exception as e:
        logger.warning(f"Failed to save to keychain: {e}")
        return False


def delete_token_from_keychain() -> bool:
    """Delete AuthKit token from OS keychain.
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        import keyring
        keyring.delete_password(KEYCHAIN_SERVICE, KEYCHAIN_USERNAME)
        logger.info("✅ Deleted AuthKit token from keychain")
        return True
    except ImportError:
        logger.debug("keyring not available, cannot delete from keychain")
        return False
    except Exception as e:
        logger.warning(f"Failed to delete from keychain: {e}")
        return False


def is_token_expired(token: str, buffer_seconds: int = TOKEN_REFRESH_BUFFER_SECONDS) -> Tuple[bool, Optional[int]]:
    """Check if a JWT token is expired or about to expire.
    
    Args:
        token: JWT token string
        buffer_seconds: Refresh if token expires within this many seconds
        
    Returns:
        Tuple of (is_expired_or_expiring_soon, expiration_timestamp)
        Returns (True, None) if token cannot be decoded
    """
    try:
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")
        
        if not exp:
            # No expiration claim - assume valid but log warning
            logger.warning("Token has no expiration claim, assuming valid")
            return (False, None)
        
        current_time = int(time.time())
        expires_at = exp
        time_until_expiry = expires_at - current_time
        
        # Check if expired or expiring soon
        is_expiring = time_until_expiry <= buffer_seconds
        
        if is_expiring:
            exp_datetime = datetime.fromtimestamp(expires_at)
            logger.info(f"Token expires at {exp_datetime} ({time_until_expiry}s remaining)")
        
        return (is_expiring, expires_at)
    except Exception as e:
        logger.warning(f"Could not decode token to check expiration: {e}")
        return (True, None)  # Assume expired if we can't decode


def refresh_token_if_needed(token: Optional[str] = None) -> Optional[str]:
    """Refresh AuthKit token if it's expired or about to expire.
    
    This function:
    1. Gets current token from keychain or environment (if not provided)
    2. Checks if it's expired or expiring soon
    3. If so, triggers a new token collection via Playwright
    4. Updates keychain with new token
    
    Args:
        token: Optional token to check. If None, retrieves from keychain/env
               (without checking expiration to avoid recursion).
        
    Returns:
        Valid (non-expired) token string, or None if refresh failed
    """
    if token is None:
        # Get token without expiration check to avoid recursion
        token = get_token_from_keychain()
        if not token:
            token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
            if token and not (len(token) >= 100 and token.count(".") >= 2):
                token = None
    
    if not token:
        logger.info("No token found, will need to collect new one")
        return None
    
    # Check expiration
    is_expiring, expires_at = is_token_expired(token)
    
    if not is_expiring:
        logger.debug("Token is still valid, no refresh needed")
        return token
    
    # Token is expired or expiring soon - need to refresh
    logger.info("Token expired or expiring soon, refreshing...")
    
    # Try to collect new token via Playwright
    try:
        import sys
        from pathlib import Path
        
        scripts_dir = Path(__file__).parent
        playwright_script = scripts_dir / "get_authkit_token_playwright.py"
        
        if not playwright_script.exists():
            logger.warning("Playwright script not found, cannot refresh token")
            return token  # Return old token as fallback
        
        # Import and run Playwright collection
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "get_authkit_token_playwright",
            playwright_script
        )
        playwright_module = importlib.util.module_from_spec(spec)
        sys.modules["get_authkit_token_playwright"] = playwright_module
        spec.loader.exec_module(playwright_module)
        
        # Run in headless mode for refresh
        original_headless = os.getenv("HEADLESS")
        os.environ["HEADLESS"] = "true"
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                new_token = loop.run_until_complete(
                    playwright_module.get_authkit_token_via_playwright()
                )
                if new_token:
                    # Save new token to keychain
                    save_token_to_keychain(new_token)
                    logger.info("✅ Token refreshed and saved to keychain")
                    return new_token
                else:
                    logger.warning("Token refresh failed, using old token")
                    return token  # Fall back to old token
            finally:
                loop.close()
        finally:
            if original_headless is None:
                os.environ.pop("HEADLESS", None)
            else:
                os.environ["HEADLESS"] = original_headless
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}, using existing token")
        import traceback
        logger.debug(traceback.format_exc())
        return token  # Fall back to existing token
    
    return token


def get_token(force_refresh: bool = False) -> Optional[str]:
    """Get AuthKit token from keychain or environment variables.
    
    Checks in order:
    1. OS keychain (most secure, persistent)
    2. ATOMS_TEST_AUTH_TOKEN environment variable
    3. AUTHKIT_TOKEN environment variable
    
    If token is expired or about to expire, automatically refreshes it.
    
    Args:
        force_refresh: If True, always refresh token even if not expired
        
    Returns:
        JWT token string if found, None otherwise
    """
    # Try keychain first
    token = get_token_from_keychain()
    if not token:
        # Fall back to environment variables
        token = os.getenv("ATOMS_TEST_AUTH_TOKEN") or os.getenv("AUTHKIT_TOKEN")
        if token:
            # Validate it's a real JWT
            if not (len(token) >= 100 and token.count(".") >= 2):
                token = None
    
    if not token:
        return None
    
    # Check expiration and refresh if needed
    if force_refresh:
        logger.info("Force refresh requested, refreshing token...")
        return refresh_token_if_needed(token)
    
    is_expiring, expires_at = is_token_expired(token)
    if is_expiring:
        logger.info("Token expired or expiring soon, refreshing...")
        return refresh_token_if_needed(token)
    
    return token


def save_token(token: str, also_to_env: bool = False) -> bool:
    """Save AuthKit token to keychain and optionally to environment.
    
    Args:
        token: JWT token string to save
        also_to_env: If True, also set ATOMS_TEST_AUTH_TOKEN environment variable
        
    Returns:
        True if saved successfully, False otherwise
    """
    success = save_token_to_keychain(token)
    
    if also_to_env:
        os.environ["ATOMS_TEST_AUTH_TOKEN"] = token
    
    return success
