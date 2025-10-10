"""Simple string templating."""

import re
from typing import Dict, Any


class Template:
    """
    Simple string template with variable substitution.

    Example:
        template = Template("Hello, {name}! You have {count} messages.")
        result = template.render(name="John", count=5)
        # "Hello, John! You have 5 messages."
    """

    def __init__(self, template: str, opener: str = '{', closer: str = '}'):
        """
        Initialize template.

        Args:
            template: Template string
            opener: Opening delimiter
            closer: Closing delimiter
        """
        self.template = template
        self.opener = re.escape(opener)
        self.closer = re.escape(closer)

    def render(self, **kwargs: Any) -> str:
        """
        Render template with variables.

        Args:
            **kwargs: Template variables

        Returns:
            Rendered string
        """
        result = self.template

        for key, value in kwargs.items():
            pattern = f"{self.opener}{key}{self.closer}"
            result = result.replace(pattern, str(value))

        return result


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Quick template rendering function.

    Example:
        render_template("Hello, {name}!", {"name": "World"})
        # "Hello, World!"

    Args:
        template: Template string
        variables: Template variables

    Returns:
        Rendered string
    """
    return Template(template).render(**variables)


def interpolate(text: str, **kwargs: Any) -> str:
    """
    Interpolate variables into string.

    Example:
        interpolate("Value: {x}", x=10)  # "Value: 10"

    Args:
        text: Text with placeholders
        **kwargs: Variables to interpolate

    Returns:
        Interpolated string
    """
    return text.format(**kwargs)
