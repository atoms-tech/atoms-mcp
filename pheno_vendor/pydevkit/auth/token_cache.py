"""
Token caching and encrypted storage.

Provides secure token storage with optional encryption.
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class CachedToken:
    """Cached token with metadata."""

    token: str
    token_type: str = "Bearer"
    expires_at: Optional[float] = None
    scope: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if token is expired.

        Args:
            buffer_seconds: Consider expired this many seconds early

        Returns:
            True if expired or will expire within buffer
        """
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedToken":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class TokenCache:
    """
    In-memory token cache with TTL support.

    Example:
        cache = TokenCache()

        # Store token
        cache.set(
            "user123",
            token="abc123",
            expires_in=3600
        )

        # Retrieve token
        cached = cache.get("user123")
        if cached and not cached.is_expired():
            print(cached.token)
    """

    def __init__(self):
        """Initialize token cache."""
        self._cache: Dict[str, CachedToken] = {}

    def set(
        self,
        key: str,
        token: str,
        token_type: str = "Bearer",
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store token in cache.

        Args:
            key: Cache key (e.g., user ID)
            token: Access token
            token_type: Token type
            expires_in: Expiration time in seconds
            scope: Token scope
            metadata: Additional metadata
        """
        expires_at = None
        if expires_in is not None:
            expires_at = time.time() + expires_in

        cached_token = CachedToken(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
            metadata=metadata,
        )

        self._cache[key] = cached_token

    def get(self, key: str, auto_remove_expired: bool = True) -> Optional[CachedToken]:
        """
        Retrieve token from cache.

        Args:
            key: Cache key
            auto_remove_expired: Remove expired tokens automatically

        Returns:
            Cached token or None if not found/expired
        """
        cached = self._cache.get(key)

        if cached and auto_remove_expired and cached.is_expired():
            del self._cache[key]
            return None

        return cached

    def delete(self, key: str) -> None:
        """
        Remove token from cache.

        Args:
            key: Cache key
        """
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached tokens."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove all expired tokens.

        Returns:
            Number of tokens removed
        """
        expired_keys = [
            key for key, cached in self._cache.items()
            if cached.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


class EncryptedTokenStorage:
    """
    Persistent token storage with optional encryption.

    Stores tokens to disk with optional XOR encryption.
    For production use, consider using stronger encryption.

    Example:
        storage = EncryptedTokenStorage(
            storage_path=Path("~/.config/myapp/tokens.json"),
            encryption_key="my-secret-key"
        )

        # Save token
        storage.save("user123", token="abc123", expires_in=3600)

        # Load token
        cached = storage.load("user123")
    """

    def __init__(
        self,
        storage_path: Path,
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize encrypted storage.

        Args:
            storage_path: Path to storage file
            encryption_key: Optional encryption key
        """
        self.storage_path = Path(storage_path).expanduser()
        self.encryption_key = encryption_key

    def _encrypt(self, data: str) -> str:
        """Encrypt data using XOR cipher."""
        if not self.encryption_key:
            return data

        key = self.encryption_key.encode('utf-8')
        data_bytes = data.encode('utf-8')

        encrypted = bytearray()
        for i, byte in enumerate(data_bytes):
            encrypted.append(byte ^ key[i % len(key)])

        import base64
        return base64.b64encode(encrypted).decode('ascii')

    def _decrypt(self, data: str) -> str:
        """Decrypt data using XOR cipher."""
        if not self.encryption_key:
            return data

        import base64
        encrypted = base64.b64decode(data)

        key = self.encryption_key.encode('utf-8')

        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            decrypted.append(byte ^ key[i % len(key)])

        return decrypted.decode('utf-8')

    def save(
        self,
        key: str,
        token: str,
        token_type: str = "Bearer",
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save token to storage.

        Args:
            key: Storage key
            token: Access token
            token_type: Token type
            expires_in: Expiration in seconds
            scope: Token scope
            metadata: Additional metadata
        """
        # Load existing tokens
        all_tokens = self._load_all()

        # Create cached token
        expires_at = None
        if expires_in is not None:
            expires_at = time.time() + expires_in

        cached_token = CachedToken(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope,
            metadata=metadata,
        )

        # Update
        all_tokens[key] = cached_token.to_dict()

        # Save
        self._save_all(all_tokens)

    def load(self, key: str) -> Optional[CachedToken]:
        """
        Load token from storage.

        Args:
            key: Storage key

        Returns:
            Cached token or None
        """
        all_tokens = self._load_all()
        token_data = all_tokens.get(key)

        if not token_data:
            return None

        cached = CachedToken.from_dict(token_data)

        # Check expiration
        if cached.is_expired():
            self.delete(key)
            return None

        return cached

    def delete(self, key: str) -> None:
        """
        Delete token from storage.

        Args:
            key: Storage key
        """
        all_tokens = self._load_all()
        if key in all_tokens:
            del all_tokens[key]
            self._save_all(all_tokens)

    def clear(self) -> None:
        """Clear all tokens."""
        self._save_all({})

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        """Load all tokens from storage."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path) as f:
                data = f.read()

            # Decrypt if needed
            data = self._decrypt(data)

            return json.loads(data)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_all(self, tokens: Dict[str, Dict[str, Any]]) -> None:
        """Save all tokens to storage."""
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to JSON
        data = json.dumps(tokens, indent=2)

        # Encrypt if needed
        data = self._encrypt(data)

        # Save
        with open(self.storage_path, 'w') as f:
            f.write(data)

        # Set restrictive permissions
        try:
            import os
            os.chmod(self.storage_path, 0o600)
        except (OSError, AttributeError):
            pass


__all__ = [
    "CachedToken",
    "TokenCache",
    "EncryptedTokenStorage",
]
