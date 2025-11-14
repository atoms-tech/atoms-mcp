"""Entity utility functions."""

import re


slug_pattern = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Convert a string to a URL-friendly slug."""
    if value is None:
        return "document"
    slug = slug_pattern.sub("-", value.strip().lower()).strip("-")
    return slug or "document"
