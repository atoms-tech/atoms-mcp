"""Common validators."""

import re
from typing import Optional


def is_email(email: str) -> bool:
    """Validate email address."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_url(url: str) -> bool:
    """Validate URL."""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def is_phone(phone: str) -> bool:
    """Validate phone number (basic US format)."""
    pattern = r'^\+?1?\d{10,15}$'
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(pattern, cleaned))


def is_ipv4(ip: str) -> bool:
    """Validate IPv4 address."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    return all(0 <= int(part) <= 255 for part in ip.split('.'))


def is_ipv6(ip: str) -> bool:
    """Validate IPv6 address (simplified)."""
    pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'
    return bool(re.match(pattern, ip))


def validate_email(email: str) -> Optional[str]:
    """Validate email, return cleaned or None."""
    email = email.strip().lower()
    return email if is_email(email) else None


def validate_url(url: str) -> Optional[str]:
    """Validate URL, return cleaned or None."""
    url = url.strip()
    return url if is_url(url) else None


def validate_phone(phone: str) -> Optional[str]:
    """Validate phone, return cleaned or None."""
    return phone if is_phone(phone) else None
