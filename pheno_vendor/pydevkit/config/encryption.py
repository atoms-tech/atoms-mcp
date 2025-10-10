"""Configuration encryption utilities with secure and fallback implementations."""

from __future__ import annotations

import base64
import logging
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

SENSITIVE_FIELD_NAMES: Set[str] = {
    "api_key",
    "api_secret",
    "secret_key",
    "password",
    "token",
    "auth_token",
    "access_token",
    "refresh_token",
    "jwt_secret",
    "database_url",
    "db_password",
    "private_key",
    "client_secret",
    "webhook_secret",
}

try:  # pragma: no cover - optional dependency
    from cryptography.fernet import Fernet

    HAS_CRYPTOGRAPHY = True
except Exception:  # pragma: no cover - optional dependency
    Fernet = None  # type: ignore
    HAS_CRYPTOGRAPHY = False


class ConfigEncryptionError(Exception):
    """Raised when configuration encryption operations fail."""


class _FallbackConfigEncryption:
    """Lightweight XOR/base64 obfuscation for environments without cryptography."""

    PREFIX = "enc:"

    def __init__(self, key: Optional[str] = None):
        self.key = key or os.getenv("CONFIG_ENCRYPTION_KEY", "default-key")

    def encrypt(self, value: str) -> str:
        if not value or value.startswith(self.PREFIX):
            return value

        key_bytes = self.key.encode("utf-8")
        value_bytes = value.encode("utf-8")

        encrypted = bytearray()
        for i, b in enumerate(value_bytes):
            encrypted.append(b ^ key_bytes[i % len(key_bytes)])

        encoded = base64.b64encode(bytes(encrypted)).decode("utf-8")
        return f"{self.PREFIX}{encoded}"

    def decrypt(self, value: str) -> str:
        if not value or not value.startswith(self.PREFIX):
            return value

        encoded = value[len(self.PREFIX):]
        try:
            encrypted = base64.b64decode(encoded)
        except Exception:
            return value

        key_bytes = self.key.encode("utf-8")
        decrypted = bytearray()
        for i, b in enumerate(encrypted):
            decrypted.append(b ^ key_bytes[i % len(key_bytes)])

        return decrypted.decode("utf-8")

    def is_encrypted(self, value: str) -> bool:
        return bool(value and value.startswith(self.PREFIX))

    def encrypt_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        encrypted = config_dict.copy()
        for key, value in encrypted.items():
            if isinstance(value, str) and self._is_sensitive_key(key):
                encrypted[key] = self.encrypt(value)
            elif isinstance(value, dict):
                encrypted[key] = self.encrypt_config_dict(value)
        return encrypted

    def decrypt_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        decrypted = config_dict.copy()
        for key, value in decrypted.items():
            if isinstance(value, str) and self.is_encrypted(value):
                decrypted[key] = self.decrypt(value)
            elif isinstance(value, dict):
                decrypted[key] = self.decrypt_config_dict(value)
        return decrypted

    def validate_key(self) -> bool:
        test_value = "pydevkit-test"
        return self.decrypt(self.encrypt(test_value)) == test_value

    @staticmethod
    def generate_key() -> str:
        return base64.b64encode(secrets.token_bytes(32)).decode("utf-8")

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        lowered = key.lower()
        return any(part in lowered for part in SENSITIVE_FIELD_NAMES)


class SecureConfigEncryption:
    """Secure encryption backed by cryptography.Fernet when available."""

    ENCRYPTED_PREFIX = "enc:"

    def __init__(self, encryption_key: Optional[str] = None, key_file: Optional[str] = None):
        if not HAS_CRYPTOGRAPHY:
            raise ConfigEncryptionError(
                "Encryption dependencies not available. Install with: pip install cryptography"
            )

        self._key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self._initialize_key(encryption_key, key_file)

    def _initialize_key(self, encryption_key: Optional[str], key_file: Optional[str]) -> None:
        key_source = None

        if encryption_key:
            key_source = "parameter"
            self._key = self._decode_key(encryption_key)
        elif os.getenv("CONFIG_ENCRYPTION_KEY"):
            key_source = "environment"
            self._key = self._decode_key(os.getenv("CONFIG_ENCRYPTION_KEY"))
        elif key_file and Path(key_file).exists():
            key_source = "file"
            self._key = self._load_key_from_file(key_file)
        elif os.getenv("ENVIRONMENT", "development").lower() == "development":
            key_source = "auto-generated"
            self._key = Fernet.generate_key()
            logger.warning(
                "Auto-generated encryption key for development. Set CONFIG_ENCRYPTION_KEY for production."
            )
        else:
            raise ConfigEncryptionError(
                "No encryption key provided. Set CONFIG_ENCRYPTION_KEY or provide key_file."
            )

        self._fernet = Fernet(self._key)
        logger.info("Configuration encryption initialized with key from %s", key_source)

    def _decode_key(self, key_str: Optional[str]) -> bytes:
        if not key_str:
            raise ConfigEncryptionError("Encryption key cannot be empty")
        try:
            return base64.b64decode(key_str.encode("utf-8"))
        except Exception as exc:
            raise ConfigEncryptionError(f"Invalid encryption key format: {exc}") from exc

    def _load_key_from_file(self, key_file: str) -> bytes:
        try:
            data = Path(key_file).read_bytes()
            try:
                return base64.b64decode(data)
            except Exception:
                return data
        except Exception as exc:
            raise ConfigEncryptionError(f"Failed to load encryption key from file: {exc}") from exc

    @classmethod
    def generate_key(cls) -> str:
        if not HAS_CRYPTOGRAPHY:
            raise ConfigEncryptionError("Encryption dependencies not available")
        key = Fernet.generate_key()
        return base64.b64encode(key).decode("utf-8")

    def encrypt(self, value: str) -> str:
        if not value or self.is_encrypted(value):
            return value
        try:
            encrypted = self._fernet.encrypt(value.encode("utf-8"))  # type: ignore[arg-type]
            encoded = base64.b64encode(encrypted).decode("utf-8")
            return f"{self.ENCRYPTED_PREFIX}{encoded}"
        except Exception as exc:
            raise ConfigEncryptionError(f"Failed to encrypt value: {exc}") from exc

    def decrypt(self, value: str) -> str:
        if not value or not self.is_encrypted(value):
            return value
        try:
            data = value[len(self.ENCRYPTED_PREFIX):] if value.startswith(self.ENCRYPTED_PREFIX) else value
            decrypted = self._fernet.decrypt(base64.b64decode(data.encode("utf-8")))  # type: ignore[arg-type]
            return decrypted.decode("utf-8")
        except Exception as exc:
            raise ConfigEncryptionError(f"Failed to decrypt value: {exc}") from exc

    def is_encrypted(self, value: str) -> bool:
        return bool(value and value.startswith(self.ENCRYPTED_PREFIX))

    def encrypt_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        encrypted = config_dict.copy()
        for key, value in encrypted.items():
            if isinstance(value, dict):
                encrypted[key] = self.encrypt_config_dict(value)
            elif isinstance(value, str) and self._is_sensitive_key(key):
                encrypted[key] = self.encrypt(value)
        return encrypted

    def decrypt_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        decrypted = config_dict.copy()
        for key, value in decrypted.items():
            if isinstance(value, dict):
                decrypted[key] = self.decrypt_config_dict(value)
            elif isinstance(value, str) and self.is_encrypted(value):
                decrypted[key] = self.decrypt(value)
        return decrypted

    def validate_key(self) -> bool:
        test_value = "pydevkit-test"
        return self.decrypt(self.encrypt(test_value)) == test_value

    def _is_sensitive_key(self, key: str) -> bool:
        lowered = key.lower()
        return any(part in lowered for part in SENSITIVE_FIELD_NAMES)


def get_config_encryptor(auto_create: bool = True) -> Optional[object]:
    """Get an appropriate ConfigEncryption instance based on environment."""
    if HAS_CRYPTOGRAPHY and auto_create:
        try:
            return SecureConfigEncryption()
        except ConfigEncryptionError as exc:
            logger.error("Failed to initialize secure config encryption: %s", exc)

    if auto_create:
        return _FallbackConfigEncryption()

    return None


def encrypt_value(value: str, key: Optional[str] = None) -> str:
    """Encrypt configuration value using best available implementation."""
    encryptor = SecureConfigEncryption(encryption_key=key) if HAS_CRYPTOGRAPHY else _FallbackConfigEncryption(key)
    return encryptor.encrypt(value)


def decrypt_value(value: str, key: Optional[str] = None) -> str:
    """Decrypt configuration value using best available implementation."""
    encryptor = SecureConfigEncryption(encryption_key=key) if HAS_CRYPTOGRAPHY else _FallbackConfigEncryption(key)
    return encryptor.decrypt(value)


def encrypt_config_dict(config_dict: Dict[str, Any], key: Optional[str] = None) -> Dict[str, Any]:
    encryptor = SecureConfigEncryption(encryption_key=key) if HAS_CRYPTOGRAPHY else _FallbackConfigEncryption(key)
    return encryptor.encrypt_config_dict(config_dict)


def decrypt_config_dict(config_dict: Dict[str, Any], key: Optional[str] = None) -> Dict[str, Any]:
    encryptor = SecureConfigEncryption(encryption_key=key) if HAS_CRYPTOGRAPHY else _FallbackConfigEncryption(key)
    return encryptor.decrypt_config_dict(config_dict)


# Default export used by existing imports
ConfigEncryption = SecureConfigEncryption if HAS_CRYPTOGRAPHY else _FallbackConfigEncryption

__all__ = [
    "ConfigEncryption",
    "ConfigEncryptionError",
    "SecureConfigEncryption",
    "encrypt_value",
    "decrypt_value",
    "encrypt_config_dict",
    "decrypt_config_dict",
    "get_config_encryptor",
    "HAS_CRYPTOGRAPHY",
]
