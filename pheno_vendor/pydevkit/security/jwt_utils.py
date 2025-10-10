"""JWT utilities (zero-dependency implementation)."""

import json
import hmac
import hashlib
import base64
import time
from typing import Any, Dict, Optional


class JWTError(Exception):
    """JWT operation error."""
    pass


def _b64_encode(data: bytes) -> str:
    """Base64url encode."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _b64_decode(data: str) -> bytes:
    """Base64url decode."""
    # Add padding
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def create_jwt(
    payload: Dict[str, Any],
    secret: str,
    algorithm: str = 'HS256',
    expires_in: Optional[int] = None,
) -> str:
    """
    Create JWT token.

    Args:
        payload: Token payload (claims)
        secret: Secret key for signing
        algorithm: Signing algorithm (HS256, HS512)
        expires_in: Expiration time in seconds

    Returns:
        JWT token string

    Example:
        token = create_jwt({'user_id': 123}, secret='my-secret', expires_in=3600)
    """
    # Add standard claims
    now = int(time.time())
    payload = payload.copy()
    payload['iat'] = now  # Issued at

    if expires_in:
        payload['exp'] = now + expires_in  # Expiration

    # Create header
    header = {
        'typ': 'JWT',
        'alg': algorithm,
    }

    # Encode header and payload
    header_encoded = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_encoded = _b64_encode(json.dumps(payload).encode('utf-8'))

    # Create signature
    message = f"{header_encoded}.{payload_encoded}"

    if algorithm == 'HS256':
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    elif algorithm == 'HS512':
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha512
        ).digest()
    else:
        raise JWTError(f"Unsupported algorithm: {algorithm}")

    signature_encoded = _b64_encode(signature)

    return f"{message}.{signature_encoded}"


def verify_jwt(token: str, secret: str, algorithms: Optional[list[str]] = None) -> Dict[str, Any]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string
        secret: Secret key for verification
        algorithms: Allowed algorithms (default: ['HS256', 'HS512'])

    Returns:
        Decoded payload

    Raises:
        JWTError: If token is invalid or expired
    """
    if algorithms is None:
        algorithms = ['HS256', 'HS512']

    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 3:
            raise JWTError("Invalid token format")

        header_encoded, payload_encoded, signature_encoded = parts

        # Decode header
        header = json.loads(_b64_decode(header_encoded))
        algorithm = header.get('alg')

        if algorithm not in algorithms:
            raise JWTError(f"Algorithm not allowed: {algorithm}")

        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"

        if algorithm == 'HS256':
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        elif algorithm == 'HS512':
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha512
            ).digest()
        else:
            raise JWTError(f"Unsupported algorithm: {algorithm}")

        actual_signature = _b64_decode(signature_encoded)

        if not hmac.compare_digest(expected_signature, actual_signature):
            raise JWTError("Invalid signature")

        # Decode payload
        payload = json.loads(_b64_decode(payload_encoded))

        # Check expiration
        if 'exp' in payload:
            if time.time() > payload['exp']:
                raise JWTError("Token expired")

        return payload

    except JWTError:
        raise
    except Exception as e:
        raise JWTError(f"Token verification failed: {e}")


def decode_jwt(token: str, verify: bool = False) -> Dict[str, Any]:
    """
    Decode JWT token without verification.

    Args:
        token: JWT token string
        verify: Whether to verify signature (requires secret)

    Returns:
        Decoded payload

    Note: Only use verify=False for debugging/inspection
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise JWTError("Invalid token format")

        payload_encoded = parts[1]
        payload = json.loads(_b64_decode(payload_encoded))

        return payload

    except Exception as e:
        raise JWTError(f"Token decoding failed: {e}")
