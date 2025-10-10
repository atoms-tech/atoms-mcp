"""Date/time parsing utilities."""

from datetime import datetime, date, time, timedelta
from typing import Optional, Union
import re


def parse_datetime(
    value: Union[str, int, float],
    formats: Optional[list[str]] = None,
) -> Optional[datetime]:
    """
    Parse datetime from various formats.

    Example:
        parse_datetime("2024-01-15 10:30:00")
        parse_datetime("2024-01-15T10:30:00Z")
        parse_datetime(1705318200)  # Unix timestamp

    Args:
        value: Value to parse (string or timestamp)
        formats: List of datetime formats to try

    Returns:
        Parsed datetime or None
    """
    # Handle timestamps
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError):
            return None

    # Default formats to try
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
        ]

    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def parse_date(value: str) -> Optional[date]:
    """
    Parse date from string.

    Example:
        parse_date("2024-01-15")
        parse_date("15/01/2024")

    Args:
        value: Date string

    Returns:
        Parsed date or None
    """
    dt = parse_datetime(value)
    return dt.date() if dt else None


def parse_time(value: str) -> Optional[time]:
    """
    Parse time from string.

    Example:
        parse_time("10:30:00")
        parse_time("10:30")

    Args:
        value: Time string

    Returns:
        Parsed time or None
    """
    formats = ['%H:%M:%S', '%H:%M', '%I:%M:%S %p', '%I:%M %p']

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.time()
        except ValueError:
            continue

    return None


def parse_duration(value: str) -> Optional[timedelta]:
    """
    Parse duration string to timedelta.

    Example:
        parse_duration("1h 30m")  # 1 hour 30 minutes
        parse_duration("2d")  # 2 days
        parse_duration("45s")  # 45 seconds

    Args:
        value: Duration string

    Returns:
        Parsed timedelta or None
    """
    pattern = r'(\d+)\s*([dhms])'
    matches = re.findall(pattern, value.lower())

    if not matches:
        return None

    total_seconds = 0

    for amount, unit in matches:
        amount = int(amount)

        if unit == 'd':
            total_seconds += amount * 86400
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 's':
            total_seconds += amount

    return timedelta(seconds=total_seconds)
