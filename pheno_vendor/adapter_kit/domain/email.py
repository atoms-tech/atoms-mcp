"""Email value object with validation."""

import re
from dataclasses import dataclass

from .value_object import ValueObject


@dataclass(frozen=True)
class Email(ValueObject):
    """Email address value object with validation.

    Example:
        >>> email = Email("user@example.com")
        >>> email.domain
        'example.com'
        >>> email.local_part
        'user'
        >>>
        >>> invalid = Email("not-an-email")  # Raises ValueError
    """

    address: str

    # Email regex pattern (simplified, covers most cases)
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __post_init__(self):
        """Validate email address."""
        if not self.EMAIL_PATTERN.match(self.address):
            raise ValueError(f"Invalid email address: {self.address}")
        self.validate()

    @property
    def local_part(self) -> str:
        """Get the local part (before @)."""
        return self.address.split("@")[0]

    @property
    def domain(self) -> str:
        """Get the domain part (after @)."""
        return self.address.split("@")[1]

    def is_company_email(self, company_domains: list[str]) -> bool:
        """Check if email belongs to company domains."""
        return self.domain.lower() in [d.lower() for d in company_domains]

    def normalize(self) -> "Email":
        """Return normalized email (lowercase)."""
        return Email(self.address.lower())

    def __str__(self) -> str:
        """String representation."""
        return self.address
