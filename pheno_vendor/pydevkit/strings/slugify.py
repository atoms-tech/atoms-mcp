"""String slugification utilities."""

import re
import unicodedata


def slugify(
    text: str,
    separator: str = '-',
    lowercase: bool = True,
    max_length: int = 0,
    word_boundary: bool = False,
) -> str:
    """
    Convert text to URL-friendly slug.

    Example:
        slugify("Hello World!")  # "hello-world"
        slugify("C'est génial!")  # "cest-genial"

    Args:
        text: Text to slugify
        separator: Character to use as separator
        lowercase: Convert to lowercase
        max_length: Maximum slug length (0 = no limit)
        word_boundary: Truncate at word boundaries

    Returns:
        Slugified string
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    # Convert to lowercase
    if lowercase:
        text = text.lower()

    # Replace spaces and special characters
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', separator, text)

    # Remove leading/trailing separators
    text = text.strip(separator)

    # Truncate if needed
    if max_length > 0 and len(text) > max_length:
        if word_boundary:
            # Find last word boundary before max_length
            truncated = text[:max_length]
            last_sep = truncated.rfind(separator)
            if last_sep > 0:
                text = truncated[:last_sep]
            else:
                text = truncated
        else:
            text = text[:max_length]

        text = text.rstrip(separator)

    return text


def slugify_filename(filename: str, max_length: int = 255) -> str:
    """
    Slugify filename while preserving extension.

    Example:
        slugify_filename("My Document (2024).pdf")  # "my-document-2024.pdf"

    Args:
        filename: Filename to slugify
        max_length: Maximum length

    Returns:
        Slugified filename
    """
    # Split name and extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = f".{ext}"
    else:
        name = filename
        ext = ''

    # Slugify name
    name = slugify(name, separator='-', lowercase=True)

    # Ensure total length doesn't exceed max
    max_name_length = max_length - len(ext)
    if len(name) > max_name_length:
        name = name[:max_name_length]

    return name + ext


def camel_to_snake(text: str) -> str:
    """
    Convert camelCase to snake_case.

    Example:
        camel_to_snake("myVariableName")  # "my_variable_name"
    """
    # Insert underscore before uppercase letters
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    return text.lower()


def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """
    Convert snake_case to camelCase.

    Example:
        snake_to_camel("my_variable_name")  # "myVariableName"
        snake_to_camel("my_variable_name", True)  # "MyVariableName"
    """
    components = text.split('_')

    if capitalize_first:
        return ''.join(x.title() for x in components)
    else:
        return components[0] + ''.join(x.title() for x in components[1:])


def kebab_to_snake(text: str) -> str:
    """Convert kebab-case to snake_case."""
    return text.replace('-', '_')


def snake_to_kebab(text: str) -> str:
    """Convert snake_case to kebab-case."""
    return text.replace('_', '-')
