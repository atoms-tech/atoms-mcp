"""Text formatting utilities."""

import textwrap
from typing import Optional


def truncate(
    text: str,
    max_length: int,
    suffix: str = '...',
    word_boundary: bool = True,
) -> str:
    """
    Truncate text to maximum length.

    Example:
        truncate("Hello World", 8)  # "Hello..."
        truncate("Hello World", 8, word_boundary=True)  # "Hello..."

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append when truncated
        word_boundary: Truncate at word boundaries

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncated_length = max_length - len(suffix)

    if word_boundary:
        # Find last space before truncation point
        truncated = text[:truncated_length]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
    else:
        truncated = text[:truncated_length]

    return truncated + suffix


def wrap_text(
    text: str,
    width: int = 70,
    indent: str = '',
    subsequent_indent: str = '',
) -> str:
    """
    Wrap text to specified width.

    Example:
        wrap_text("Long text here", width=10)

    Args:
        text: Text to wrap
        width: Maximum line width
        indent: Indent for first line
        subsequent_indent: Indent for subsequent lines

    Returns:
        Wrapped text
    """
    return textwrap.fill(
        text,
        width=width,
        initial_indent=indent,
        subsequent_indent=subsequent_indent,
    )


def pad_string(
    text: str,
    length: int,
    char: str = ' ',
    align: str = 'left',
) -> str:
    """
    Pad string to specified length.

    Example:
        pad_string("hello", 10, char='*', align='center')  # "**hello***"

    Args:
        text: Text to pad
        length: Target length
        char: Padding character
        align: Alignment (left, right, center)

    Returns:
        Padded string
    """
    if len(text) >= length:
        return text

    if align == 'left':
        return text.ljust(length, char)
    elif align == 'right':
        return text.rjust(length, char)
    elif align == 'center':
        return text.center(length, char)
    else:
        raise ValueError(f"Invalid alignment: {align}")


def remove_whitespace(text: str, keep: Optional[str] = None) -> str:
    """
    Remove whitespace from text.

    Args:
        text: Text to process
        keep: Whitespace characters to keep (e.g., ' ' to keep spaces)

    Returns:
        Text with whitespace removed
    """
    if keep is None:
        return ''.join(text.split())

    result = []
    for char in text:
        if not char.isspace() or char in keep:
            result.append(char)

    return ''.join(result)


def indent_text(text: str, indent: str = '    ') -> str:
    """
    Indent all lines in text.

    Args:
        text: Text to indent
        indent: Indent string

    Returns:
        Indented text
    """
    return textwrap.indent(text, indent)
