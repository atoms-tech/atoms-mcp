"""Address value object."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .value_object import ValueObject


class Country(str, Enum):
    """ISO 3166-1 alpha-2 country codes."""

    US = "US"
    CA = "CA"
    GB = "GB"
    FR = "FR"
    DE = "DE"
    JP = "JP"
    CN = "CN"
    IN = "IN"
    AU = "AU"
    BR = "BR"


@dataclass(frozen=True)
class Address(ValueObject):
    """Physical address value object.

    Example:
        >>> address = Address(
        ...     street="123 Main St",
        ...     city="Springfield",
        ...     state="IL",
        ...     postal_code="62701",
        ...     country=Country.US
        ... )
        >>> address.format()
        '123 Main St, Springfield, IL 62701, US'
    """

    street: str
    city: str
    state: str
    postal_code: str
    country: Country
    street2: Optional[str] = None

    def __post_init__(self):
        """Validate address."""
        if not self.street:
            raise ValueError("Street is required")
        if not self.city:
            raise ValueError("City is required")
        if not self.postal_code:
            raise ValueError("Postal code is required")
        self.validate()

    def format(self, multiline: bool = False) -> str:
        """Format address for display.

        Args:
            multiline: If True, format across multiple lines

        Returns:
            Formatted address string
        """
        lines = [self.street]

        if self.street2:
            lines.append(self.street2)

        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country.value)

        if multiline:
            return "\n".join(lines)
        else:
            return ", ".join(lines)

    def is_us_address(self) -> bool:
        """Check if this is a US address."""
        return self.country == Country.US

    def is_same_city(self, other: "Address") -> bool:
        """Check if in the same city."""
        return (
            self.city.lower() == other.city.lower()
            and self.state.lower() == other.state.lower()
            and self.country == other.country
        )

    def __str__(self) -> str:
        """String representation."""
        return self.format()
