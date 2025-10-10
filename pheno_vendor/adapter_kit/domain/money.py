"""Money value object with currency support.

Represents monetary amounts with proper currency handling and arithmetic.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Union

from .value_object import ValueObject


class Currency(str, Enum):
    """ISO 4217 currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object with currency.

    Implements proper money arithmetic with currency checking.
    Uses Decimal for precise calculations.

    Example:
        >>> price = Money(Decimal("19.99"), Currency.USD)
        >>> tax = Money(Decimal("2.00"), Currency.USD)
        >>> total = price + tax
        >>> print(total)
        Money(amount=21.99, currency=USD)
        >>>
        >>> # Currency mismatch raises error
        >>> euro_price = Money(Decimal("15.00"), Currency.EUR)
        >>> price + euro_price  # Raises ValueError
    """

    amount: Decimal
    currency: Currency

    def __post_init__(self):
        """Validate money invariants."""
        if not isinstance(self.amount, Decimal):
            raise TypeError("Amount must be a Decimal")
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        self.validate()

    def __add__(self, other: "Money") -> "Money":
        """Add two money amounts (must have same currency)."""
        self._check_currency_compatibility(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two money amounts (must have same currency)."""
        self._check_currency_compatibility(other)
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(result, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> "Money":
        """Multiply money by a scalar."""
        if not isinstance(multiplier, (int, float, Decimal)):
            raise TypeError("Can only multiply money by a number")
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> "Money":
        """Divide money by a scalar."""
        if not isinstance(divisor, (int, float, Decimal)):
            raise TypeError("Can only divide money by a number")
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._check_currency_compatibility(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._check_currency_compatibility(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._check_currency_compatibility(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._check_currency_compatibility(other)
        return self.amount >= other.amount

    def _check_currency_compatibility(self, other: "Money") -> None:
        """Ensure currencies match for operations."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot operate on different currencies: {self.currency} and {other.currency}"
            )

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0")

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > Decimal("0")

    def round_to_cents(self) -> "Money":
        """Round to 2 decimal places (cents)."""
        rounded = self.amount.quantize(Decimal("0.01"))
        return Money(rounded, self.currency)

    def format(self) -> str:
        """Format money for display."""
        symbols = {
            Currency.USD: "$",
            Currency.EUR: "€",
            Currency.GBP: "£",
            Currency.JPY: "¥",
            Currency.CNY: "¥",
            Currency.INR: "₹",
            Currency.CAD: "C$",
            Currency.AUD: "A$",
            Currency.CHF: "CHF ",
        }
        symbol = symbols.get(self.currency, self.currency.value + " ")
        return f"{symbol}{self.amount:.2f}"

    def __str__(self) -> str:
        """String representation."""
        return self.format()

    @classmethod
    def zero(cls, currency: Currency) -> "Money":
        """Create a zero money amount."""
        return cls(Decimal("0"), currency)

    @classmethod
    def from_float(cls, amount: float, currency: Currency) -> "Money":
        """Create from float (use with caution, prefer Decimal)."""
        return cls(Decimal(str(amount)), currency)
