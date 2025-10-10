"""Security filter for sanitizing sensitive information from logs.

Provides comprehensive PII and secrets redaction for structured logging.
"""

import logging
import re
from typing import List, Pattern, Optional


class SecurityFilter(logging.Filter):
    """Filter to sanitize sensitive information from log records.

    This filter automatically redacts:
    - Passwords, secrets, tokens, API keys
    - Authorization headers and bearer tokens
    - Email addresses (partial masking)
    - Credit card numbers
    - Social Security Numbers
    - Phone numbers
    - IP addresses (optional)
    - Custom patterns

    Example:
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> handler = logging.StreamHandler()
        >>> handler.addFilter(SecurityFilter())
        >>> logger.addHandler(handler)
    """

    def __init__(
        self,
        *,
        redact_emails: bool = True,
        redact_ips: bool = False,
        redact_credit_cards: bool = True,
        redact_ssn: bool = True,
        redact_phone: bool = True,
        custom_patterns: Optional[List[str]] = None,
        replacement: str = "[REDACTED]",
    ):
        """Initialize security filter.

        Args:
            redact_emails: Redact email addresses
            redact_ips: Redact IP addresses
            redact_credit_cards: Redact credit card numbers
            redact_ssn: Redact Social Security Numbers
            redact_phone: Redact phone numbers
            custom_patterns: Additional regex patterns to redact
            replacement: Replacement text for redacted content
        """
        super().__init__()
        self.replacement = replacement
        self.patterns: List[Pattern] = []

        # Core security patterns (always enabled)
        self._add_core_patterns()

        # Optional patterns
        if redact_emails:
            self._add_email_patterns()

        if redact_ips:
            self._add_ip_patterns()

        if redact_credit_cards:
            self._add_credit_card_patterns()

        if redact_ssn:
            self._add_ssn_patterns()

        if redact_phone:
            self._add_phone_patterns()

        # Custom patterns
        if custom_patterns:
            for pattern in custom_patterns:
                self.patterns.append(re.compile(pattern, re.IGNORECASE))

    def _add_core_patterns(self) -> None:
        """Add core security patterns (passwords, secrets, tokens, keys)."""
        core_patterns = [
            # Passwords and secrets in various formats
            r'password["\s]*[:=]["\s]*([^"\s\n]+)',
            r'secret["\s]*[:=]["\s]*([^"\s\n]+)',
            r'token["\s]*[:=]["\s]*([^"\s\n]+)',
            r'api[_-]?key["\s]*[:=]["\s]*([^"\s\n]+)',
            r'private[_-]?key["\s]*[:=]["\s]*([^"\s\n]+)',
            r'access[_-]?key["\s]*[:=]["\s]*([^"\s\n]+)',
            r'secret[_-]?key["\s]*[:=]["\s]*([^"\s\n]+)',

            # Authorization headers
            r'authorization["\s]*:["\s]*([^"\s\n]+)',
            r'bearer\s+([a-zA-Z0-9\.\-_]+)',
            r'basic\s+([a-zA-Z0-9\+/=]+)',

            # AWS credentials
            r'aws[_-]?access[_-]?key[_-]?id["\s]*[:=]["\s]*([A-Z0-9]{20})',
            r'aws[_-]?secret[_-]?access[_-]?key["\s]*[:=]["\s]*([A-Za-z0-9/+=]{40})',

            # Database connection strings
            r'(mysql|postgresql|mongodb|redis)://[^:]+:([^@]+)@',
            r'://[^:]+:([^@]+)@[^/]+',

            # Generic API keys (hex, base64)
            r'\b[A-Fa-f0-9]{32,64}\b',  # Hex keys
            r'\b[A-Za-z0-9+/]{40,}\b',  # Base64 keys

            # JSON Web Tokens
            r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        ]

        for pattern in core_patterns:
            self.patterns.append(re.compile(pattern, re.IGNORECASE))

    def _add_email_patterns(self) -> None:
        """Add email redaction patterns."""
        email_patterns = [
            # Standard email format
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ]

        for pattern in email_patterns:
            self.patterns.append(re.compile(pattern, re.IGNORECASE))

    def _add_ip_patterns(self) -> None:
        """Add IP address redaction patterns."""
        ip_patterns = [
            # IPv4
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            # IPv6
            r'\b(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}\b',
        ]

        for pattern in ip_patterns:
            self.patterns.append(re.compile(pattern, re.IGNORECASE))

    def _add_credit_card_patterns(self) -> None:
        """Add credit card number redaction patterns."""
        cc_patterns = [
            # Credit card with spaces or dashes
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            # Credit card without separators
            r'\b\d{13,19}\b',
        ]

        for pattern in cc_patterns:
            self.patterns.append(re.compile(pattern))

    def _add_ssn_patterns(self) -> None:
        """Add Social Security Number redaction patterns."""
        ssn_patterns = [
            # SSN with dashes
            r'\b\d{3}-\d{2}-\d{4}\b',
            # SSN without dashes
            r'\b\d{9}\b',
        ]

        for pattern in ssn_patterns:
            self.patterns.append(re.compile(pattern))

    def _add_phone_patterns(self) -> None:
        """Add phone number redaction patterns."""
        phone_patterns = [
            # US phone numbers
            r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            # International format
            r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',
        ]

        for pattern in phone_patterns:
            self.patterns.append(re.compile(pattern))

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text by applying all redaction patterns."""
        if not isinstance(text, str):
            return text

        sanitized = text
        for pattern in self.patterns:
            sanitized = pattern.sub(self.replacement, sanitized)

        return sanitized

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize sensitive information from log record.

        Args:
            record: Log record to filter

        Returns:
            True to allow the record to be logged
        """
        # Sanitize the message
        if hasattr(record, "msg") and isinstance(record.msg, str):
            record.msg = self._sanitize_text(record.msg)

        # Sanitize arguments
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._sanitize_text(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize_text(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        # Sanitize extra attributes (passed via extra={})
        excluded_keys = {
            "name", "levelname", "pathname", "filename",
            "module", "funcName", "levelno", "lineno",
        }

        for key, value in list(record.__dict__.items()):
            if key not in excluded_keys and isinstance(value, str):
                setattr(record, key, self._sanitize_text(value))
            elif key not in excluded_keys and isinstance(value, dict):
                setattr(
                    record,
                    key,
                    {
                        k: self._sanitize_text(v) if isinstance(v, str) else v
                        for k, v in value.items()
                    },
                )

        return True


def create_security_filter(
    *,
    redact_emails: bool = True,
    redact_ips: bool = False,
    custom_patterns: Optional[List[str]] = None,
) -> SecurityFilter:
    """Factory function to create a configured security filter.

    Args:
        redact_emails: Redact email addresses
        redact_ips: Redact IP addresses
        custom_patterns: Additional regex patterns to redact

    Returns:
        Configured SecurityFilter instance

    Example:
        >>> filter = create_security_filter(redact_ips=True)
        >>> handler.addFilter(filter)
    """
    return SecurityFilter(
        redact_emails=redact_emails,
        redact_ips=redact_ips,
        custom_patterns=custom_patterns,
    )


__all__ = ["SecurityFilter", "create_security_filter"]
