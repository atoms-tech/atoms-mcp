"""Simple encryption utilities (XOR-based obfuscation for zero-dependency)."""

import base64
import secrets
from typing import Optional


def generate_key(length: int = 32) -> str:
    """
    Generate encryption key.

    Args:
        length: Key length in bytes

    Returns:
        Base64-encoded key
    """
    return base64.b64encode(secrets.token_bytes(length)).decode('utf-8')


def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt plaintext using XOR cipher.

    Note: This is simple obfuscation, NOT cryptographically secure.
    For production, use cryptography library with AES-GCM.

    Args:
        plaintext: Text to encrypt
        key: Encryption key

    Returns:
        Base64-encoded ciphertext
    """
    key_bytes = key.encode('utf-8')
    plaintext_bytes = plaintext.encode('utf-8')

    # XOR encryption
    encrypted = bytearray()
    for i, byte in enumerate(plaintext_bytes):
        encrypted.append(byte ^ key_bytes[i % len(key_bytes)])

    return base64.b64encode(bytes(encrypted)).decode('utf-8')


def decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt ciphertext.

    Args:
        ciphertext: Base64-encoded ciphertext
        key: Encryption key

    Returns:
        Decrypted plaintext
    """
    key_bytes = key.encode('utf-8')
    encrypted_bytes = base64.b64decode(ciphertext)

    # XOR decryption (same as encryption)
    decrypted = bytearray()
    for i, byte in enumerate(encrypted_bytes):
        decrypted.append(byte ^ key_bytes[i % len(key_bytes)])

    return bytes(decrypted).decode('utf-8')


def encrypt_dict(data: dict, key: str, sensitive_keys: Optional[set] = None) -> dict:
    """
    Encrypt sensitive values in dictionary.

    Args:
        data: Dictionary to encrypt
        key: Encryption key
        sensitive_keys: Keys to encrypt (if None, encrypts all string values)

    Returns:
        Dictionary with encrypted values
    """
    result = {}

    for k, v in data.items():
        if isinstance(v, dict):
            result[k] = encrypt_dict(v, key, sensitive_keys)
        elif isinstance(v, str):
            if sensitive_keys is None or k in sensitive_keys:
                result[k] = encrypt(v, key)
            else:
                result[k] = v
        else:
            result[k] = v

    return result


def decrypt_dict(data: dict, key: str, sensitive_keys: Optional[set] = None) -> dict:
    """
    Decrypt sensitive values in dictionary.

    Args:
        data: Dictionary to decrypt
        key: Encryption key
        sensitive_keys: Keys to decrypt (if None, attempts to decrypt all string values)

    Returns:
        Dictionary with decrypted values
    """
    result = {}

    for k, v in data.items():
        if isinstance(v, dict):
            result[k] = decrypt_dict(v, key, sensitive_keys)
        elif isinstance(v, str):
            if sensitive_keys is None or k in sensitive_keys:
                try:
                    result[k] = decrypt(v, key)
                except Exception:
                    result[k] = v
            else:
                result[k] = v
        else:
            result[k] = v

    return result
