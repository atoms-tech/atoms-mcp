"""Hashing utilities for passwords and data."""

import hashlib
import secrets
import hmac
from typing import Optional


def hash_password(password: str, salt: Optional[str] = None, iterations: int = 100000) -> str:
    """
    Hash password using PBKDF2.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
        iterations: Number of iterations

    Returns:
        Hashed password in format: salt$hash
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 for password hashing
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    hash_hex = key.hex()

    return f"{salt}${hash_hex}"


def verify_password(password: str, hashed: str, iterations: int = 100000) -> bool:
    """
    Verify password against hash.

    Args:
        password: Plain text password
        hashed: Hashed password from hash_password()
        iterations: Number of iterations used in hashing

    Returns:
        True if password matches
    """
    try:
        salt, expected_hash = hashed.split('$', 1)
        actual_hash = hash_password(password, salt, iterations)
        return hmac.compare_digest(actual_hash, hashed)
    except Exception:
        return False


def hash_string(data: str, algorithm: str = 'sha256') -> str:
    """
    Hash string using specified algorithm.

    Args:
        data: String to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        Hex-encoded hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data.encode('utf-8'))
    return hasher.hexdigest()


def hash_bytes(data: bytes, algorithm: str = 'sha256') -> str:
    """Hash bytes using specified algorithm."""
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def generate_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        Hex-encoded token
    """
    return secrets.token_hex(length)


def generate_url_safe_token(length: int = 32) -> str:
    """
    Generate URL-safe random token.

    Args:
        length: Token length in bytes

    Returns:
        URL-safe base64-encoded token
    """
    return secrets.token_urlsafe(length)


def hmac_sign(message: str, secret: str, algorithm: str = 'sha256') -> str:
    """
    Create HMAC signature for message.

    Args:
        message: Message to sign
        secret: Secret key
        algorithm: Hash algorithm

    Returns:
        Hex-encoded HMAC signature
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.new(algorithm)
    )
    return signature.hexdigest()


def hmac_verify(message: str, signature: str, secret: str, algorithm: str = 'sha256') -> bool:
    """
    Verify HMAC signature.

    Args:
        message: Original message
        signature: HMAC signature to verify
        secret: Secret key
        algorithm: Hash algorithm

    Returns:
        True if signature is valid
    """
    expected = hmac_sign(message, secret, algorithm)
    return hmac.compare_digest(expected, signature)


def generate_fingerprint(data: str) -> str:
    """
    Generate short fingerprint for data.

    Args:
        data: Data to fingerprint

    Returns:
        Short hash suitable for display (12 chars)
    """
    full_hash = hash_string(data, 'sha256')
    return full_hash[:12]
