"""String sanitization utilities."""

import html as html_module
import re
from typing import Set


def sanitize_html(text: str, allowed_tags: Set[str] = None) -> str:
    """
    Sanitize HTML by escaping or removing tags.

    Example:
        sanitize_html("<script>alert('xss')</script>")  # Escaped
        sanitize_html("<p>Hello</p>", {'p'})  # "<p>Hello</p>"

    Args:
        text: Text to sanitize
        allowed_tags: Set of allowed HTML tags

    Returns:
        Sanitized text
    """
    if allowed_tags is None:
        # Escape all HTML
        return html_module.escape(text)

    # Remove disallowed tags
    def replace_tag(match):
        tag_name = match.group(1).lower().split()[0]
        if tag_name in allowed_tags:
            return match.group(0)
        return ''

    # Remove disallowed tags
    text = re.sub(r'<(/?)([^>]+)>', replace_tag, text)

    return text


def strip_tags(text: str) -> str:
    """
    Remove all HTML tags from text.

    Example:
        strip_tags("<p>Hello <b>World</b></p>")  # "Hello World"

    Args:
        text: Text with HTML tags

    Returns:
        Text without tags
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = html_module.unescape(text)

    return text


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Example:
        sanitize_filename("file:name?.txt")  # "file_name_.txt"

    Args:
        filename: Filename to sanitize
        replacement: Character to replace invalid chars with

    Returns:
        Sanitized filename
    """
    # Remove/replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Prevent reserved names on Windows
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}

    name = filename.split('.')[0].upper()
    if name in reserved:
        filename = f"{replacement}{filename}"

    return filename or 'unnamed'


def remove_control_characters(text: str) -> str:
    """
    Remove control characters from text.

    Args:
        text: Text to clean

    Returns:
        Text without control characters
    """
    # Remove control characters except newline, tab, carriage return
    return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace (convert multiple spaces to single).

    Example:
        normalize_whitespace("Hello    World")  # "Hello World"

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)

    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)

    return text.strip()


def escape_for_regex(text: str) -> str:
    """
    Escape special regex characters.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for regex
    """
    return re.escape(text)
