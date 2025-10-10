"""Timezone utilities."""

from datetime import datetime, timezone, tzinfo
from typing import Optional


def now_utc() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_timezone(dt: datetime, tz: tzinfo) -> datetime:
    """Convert datetime to specified timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def get_timezone(offset_hours: int) -> tzinfo:
    """
    Get timezone for UTC offset.

    Example:
        get_timezone(-5)  # UTC-5
    """
    from datetime import timedelta
    return timezone(timedelta(hours=offset_hours))
