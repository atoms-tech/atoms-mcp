"""
Multi-factor authentication (MFA) handlers.

Provides utilities for handling TOTP and other MFA methods.
"""

from typing import Optional, Callable
import time
import hmac
import hashlib
import base64
import struct


class TOTPHandler:
    """
    Time-based One-Time Password (TOTP) handler.

    Implements RFC 6238 TOTP algorithm for generating and validating
    time-based one-time passwords.

    Example:
        handler = TOTPHandler(secret="BASE32SECRET")

        # Generate current code
        code = handler.generate()

        # Verify code
        is_valid = handler.verify(code)
    """

    def __init__(
        self,
        secret: str,
        digits: int = 6,
        interval: int = 30,
        algorithm: str = "sha1",
    ):
        """
        Initialize TOTP handler.

        Args:
            secret: Base32-encoded secret key
            digits: Number of digits in code (default: 6)
            interval: Time interval in seconds (default: 30)
            algorithm: Hash algorithm (sha1, sha256, sha512)
        """
        self.secret = secret
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm

    def _get_secret_bytes(self) -> bytes:
        """Decode base32 secret to bytes."""
        # Add padding if needed
        missing_padding = len(self.secret) % 8
        if missing_padding:
            self.secret += '=' * (8 - missing_padding)

        try:
            return base64.b32decode(self.secret, casefold=True)
        except Exception as e:
            raise ValueError(f"Invalid base32 secret: {e}")

    def _get_counter(self, timestamp: Optional[float] = None) -> int:
        """Get time counter for timestamp."""
        if timestamp is None:
            timestamp = time.time()
        return int(timestamp) // self.interval

    def _generate_otp(self, counter: int) -> str:
        """
        Generate OTP for given counter.

        Args:
            counter: Time counter value

        Returns:
            OTP code as string
        """
        # Get hash algorithm
        hash_algos = {
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512,
        }
        hash_algo = hash_algos.get(self.algorithm.lower(), hashlib.sha1)

        # Convert counter to bytes
        counter_bytes = struct.pack('>Q', counter)

        # Generate HMAC
        secret_bytes = self._get_secret_bytes()
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hash_algo).digest()

        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0F
        code = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        code = (code & 0x7FFFFFFF) % (10 ** self.digits)

        # Pad with zeros if needed
        return str(code).zfill(self.digits)

    def generate(self, timestamp: Optional[float] = None) -> str:
        """
        Generate TOTP code for current time.

        Args:
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            TOTP code as string

        Example:
            code = handler.generate()  # "123456"
        """
        counter = self._get_counter(timestamp)
        return self._generate_otp(counter)

    def verify(
        self,
        code: str,
        timestamp: Optional[float] = None,
        window: int = 1,
    ) -> bool:
        """
        Verify TOTP code.

        Args:
            code: Code to verify
            timestamp: Optional timestamp (defaults to current time)
            window: Number of intervals to check before/after (default: 1)

        Returns:
            True if code is valid

        Example:
            is_valid = handler.verify("123456")
        """
        counter = self._get_counter(timestamp)

        # Check current and adjacent windows
        for i in range(-window, window + 1):
            if self._generate_otp(counter + i) == code:
                return True

        return False

    def get_remaining_seconds(self, timestamp: Optional[float] = None) -> int:
        """
        Get seconds remaining until next code.

        Args:
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Seconds until next interval
        """
        if timestamp is None:
            timestamp = time.time()
        return self.interval - (int(timestamp) % self.interval)


class MFAHandler:
    """
    Generic MFA handler with support for multiple methods.

    Example:
        handler = MFAHandler()

        # Register TOTP
        handler.register_totp("user@example.com", "BASE32SECRET")

        # Verify code
        is_valid = handler.verify_totp("user@example.com", "123456")
    """

    def __init__(self):
        """Initialize MFA handler."""
        self._totp_secrets: dict[str, str] = {}
        self._sms_callback: Optional[Callable[[str, str], bool]] = None

    def register_totp(self, user_id: str, secret: str) -> None:
        """
        Register TOTP secret for user.

        Args:
            user_id: User identifier
            secret: Base32-encoded TOTP secret
        """
        self._totp_secrets[user_id] = secret

    def verify_totp(
        self,
        user_id: str,
        code: str,
        window: int = 1,
    ) -> bool:
        """
        Verify TOTP code for user.

        Args:
            user_id: User identifier
            code: TOTP code to verify
            window: Time window for verification

        Returns:
            True if code is valid
        """
        secret = self._totp_secrets.get(user_id)
        if not secret:
            return False

        handler = TOTPHandler(secret)
        return handler.verify(code, window=window)

    def generate_totp(self, user_id: str) -> Optional[str]:
        """
        Generate current TOTP code for user.

        Args:
            user_id: User identifier

        Returns:
            Current TOTP code or None if not registered
        """
        secret = self._totp_secrets.get(user_id)
        if not secret:
            return None

        handler = TOTPHandler(secret)
        return handler.generate()

    def register_sms_callback(
        self,
        callback: Callable[[str, str], bool],
    ) -> None:
        """
        Register SMS verification callback.

        Args:
            callback: Function that takes (phone, code) and returns bool
        """
        self._sms_callback = callback

    def verify_sms(self, phone: str, code: str) -> bool:
        """
        Verify SMS code.

        Args:
            phone: Phone number
            code: SMS code to verify

        Returns:
            True if code is valid
        """
        if self._sms_callback:
            return self._sms_callback(phone, code)
        return False


def generate_totp_secret() -> str:
    """
    Generate a random base32-encoded TOTP secret.

    Returns:
        Base32-encoded secret suitable for TOTP

    Example:
        secret = generate_totp_secret()
        handler = TOTPHandler(secret)
    """
    import secrets

    # Generate 20 random bytes (160 bits)
    random_bytes = secrets.token_bytes(20)

    # Encode as base32
    secret = base64.b32encode(random_bytes).decode('ascii')

    # Remove padding
    return secret.rstrip('=')


__all__ = [
    "TOTPHandler",
    "MFAHandler",
    "generate_totp_secret",
]
