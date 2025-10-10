"""Date/time formatting utilities."""

from datetime import datetime, timedelta
from typing import Optional


def format_datetime(
    dt: datetime,
    format_str: str = '%Y-%m-%d %H:%M:%S',
) -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)


def format_relative(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Format datetime as relative time.

    Example:
        format_relative(datetime.now() - timedelta(minutes=5))  # "5 minutes ago"
    """
    if reference is None:
        reference = datetime.now()

    delta = reference - dt
    seconds = delta.total_seconds()

    if seconds < 0:
        return "in the future"
    elif seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def humanize_duration(seconds: float) -> str:
    """
    Convert seconds to human-readable duration.

    Example:
        humanize_duration(3665)  # "1h 1m 5s"
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"

    parts = []
    remaining = int(seconds)

    days = remaining // 86400
    if days:
        parts.append(f"{days}d")
        remaining %= 86400

    hours = remaining // 3600
    if hours:
        parts.append(f"{hours}h")
        remaining %= 3600

    minutes = remaining // 60
    if minutes:
        parts.append(f"{minutes}m")
        remaining %= 60

    if remaining or not parts:
        parts.append(f"{remaining}s")

    return ' '.join(parts)
