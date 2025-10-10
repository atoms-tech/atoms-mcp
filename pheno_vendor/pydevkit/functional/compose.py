"""Function composition utilities."""

from typing import Callable, Any
from functools import reduce


def compose(*functions: Callable) -> Callable:
    """
    Compose functions (right to left).

    Example:
        f = compose(str, lambda x: x * 2, lambda x: x + 1)
        f(5)  # "12" (5 + 1 = 6, 6 * 2 = 12, str(12) = "12")
    """
    def composed(x):
        return reduce(lambda acc, f: f(acc), reversed(functions), x)
    return composed


def pipe(*functions: Callable) -> Callable:
    """
    Pipe functions (left to right).

    Example:
        f = pipe(lambda x: x + 1, lambda x: x * 2, str)
        f(5)  # "12" (5 + 1 = 6, 6 * 2 = 12, str(12) = "12")
    """
    def piped(x):
        return reduce(lambda acc, f: f(acc), functions, x)
    return piped
