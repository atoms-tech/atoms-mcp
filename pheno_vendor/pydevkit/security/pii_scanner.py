"""PII (Personally Identifiable Information) scanner and redactor."""

import re
from typing import List, Dict, Optional, Set


class PIIPattern:
    """PII pattern definitions."""

    # Email pattern
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Phone number patterns (US format)
    PHONE = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'

    # SSN pattern (US)
    SSN = r'\b\d{3}-\d{2}-\d{4}\b'

    # Credit card pattern (basic)
    CREDIT_CARD = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'

    # IP address
    IP_ADDRESS = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'

    # API keys (generic pattern)
    API_KEY = r'\b[A-Za-z0-9]{32,}\b'


class PIIScanner:
    """
    Scan and redact PII from text.

    Example:
        scanner = PIIScanner()
        text = "Contact john@example.com or call 555-123-4567"
        redacted = scanner.redact(text)
        # "Contact [EMAIL] or call [PHONE]"
    """

    def __init__(self, custom_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize PII scanner.

        Args:
            custom_patterns: Additional PII patterns as {name: regex}
        """
        self.patterns = {
            'EMAIL': PIIPattern.EMAIL,
            'PHONE': PIIPattern.PHONE,
            'SSN': PIIPattern.SSN,
            'CREDIT_CARD': PIIPattern.CREDIT_CARD,
            'IP_ADDRESS': PIIPattern.IP_ADDRESS,
        }

        if custom_patterns:
            self.patterns.update(custom_patterns)

    def detect(self, text: str, pattern_names: Optional[Set[str]] = None) -> List[Dict[str, any]]:
        """
        Detect PII in text.

        Args:
            text: Text to scan
            pattern_names: Specific patterns to check (None = all)

        Returns:
            List of detections with {type, value, start, end}
        """
        detections = []
        patterns_to_check = pattern_names or set(self.patterns.keys())

        for name in patterns_to_check:
            if name not in self.patterns:
                continue

            pattern = self.patterns[name]
            for match in re.finditer(pattern, text):
                detections.append({
                    'type': name,
                    'value': match.group(0),
                    'start': match.start(),
                    'end': match.end(),
                })

        return detections

    def redact(
        self,
        text: str,
        pattern_names: Optional[Set[str]] = None,
        redaction_char: str = '*',
        show_type: bool = True,
    ) -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact
            pattern_names: Specific patterns to redact (None = all)
            redaction_char: Character to use for redaction
            show_type: Whether to show PII type in redaction

        Returns:
            Redacted text
        """
        detections = self.detect(text, pattern_names)

        # Sort by start position (reverse order for replacement)
        detections.sort(key=lambda x: x['start'], reverse=True)

        result = text
        for detection in detections:
            start, end = detection['start'], detection['end']

            if show_type:
                replacement = f"[{detection['type']}]"
            else:
                length = end - start
                replacement = redaction_char * length

            result = result[:start] + replacement + result[end:]

        return result

    def mask(
        self,
        text: str,
        pattern_names: Optional[Set[str]] = None,
        show_first: int = 0,
        show_last: int = 0,
        mask_char: str = '*',
    ) -> str:
        """
        Mask PII (show partial information).

        Args:
            text: Text to mask
            pattern_names: Specific patterns to mask (None = all)
            show_first: Number of characters to show at start
            show_last: Number of characters to show at end
            mask_char: Character to use for masking

        Returns:
            Masked text

        Example:
            mask("john@example.com", show_first=2, show_last=4)
            # "jo********.com"
        """
        detections = self.detect(text, pattern_names)
        detections.sort(key=lambda x: x['start'], reverse=True)

        result = text
        for detection in detections:
            start, end = detection['start'], detection['end']
            value = detection['value']

            if len(value) <= show_first + show_last:
                continue

            masked = (
                value[:show_first] +
                mask_char * (len(value) - show_first - show_last) +
                value[-show_last:] if show_last > 0 else ''
            )

            result = result[:start] + masked + result[end:]

        return result


def detect_pii(text: str, patterns: Optional[Dict[str, str]] = None) -> List[Dict[str, any]]:
    """
    Detect PII in text.

    Args:
        text: Text to scan
        patterns: Custom patterns (None = use defaults)

    Returns:
        List of PII detections
    """
    scanner = PIIScanner(patterns)
    return scanner.detect(text)


def redact_pii(text: str, show_type: bool = True) -> str:
    """
    Redact PII from text.

    Args:
        text: Text to redact
        show_type: Whether to show PII type

    Returns:
        Redacted text
    """
    scanner = PIIScanner()
    return scanner.redact(text, show_type=show_type)


def mask_email(email: str) -> str:
    """
    Mask email address.

    Example: john.doe@example.com -> j******e@example.com
    """
    if '@' not in email:
        return email

    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number.

    Example: 555-123-4567 -> ***-***-4567
    """
    # Keep only last 4 digits
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) < 4:
        return '*' * len(phone)

    return '*' * (len(phone) - 4) + phone[-4:]
