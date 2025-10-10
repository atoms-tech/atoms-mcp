"""Retry strategies for HTTP requests."""

import random
import time
from functools import wraps
from typing import Callable, Optional, Set, TypeVar

T = TypeVar('T')


class RetryStrategy:
    """
    Configurable retry strategy with exponential backoff.

    Example:
        strategy = RetryStrategy(max_attempts=3, backoff_factor=2.0)
        result = strategy.execute(lambda: make_request())
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retry_on_status: Optional[Set[int]] = None,
        retry_on_exceptions: Optional[tuple] = None,
    ):
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            backoff_factor: Multiplier for delay between retries
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            jitter: Add random jitter to delays
            retry_on_status: HTTP status codes to retry on (default: {429, 500, 502, 503, 504})
            retry_on_exceptions: Exception types to retry on
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_on_status = retry_on_status or {429, 500, 502, 503, 504}
        self.retry_on_exceptions = retry_on_exceptions or (ConnectionError, TimeoutError)

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def should_retry(self, attempt: int, exception: Optional[Exception] = None, status_code: Optional[int] = None) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.max_attempts:
            return False

        if status_code is not None and status_code in self.retry_on_status:
            return True

        if exception is not None and isinstance(exception, self.retry_on_exceptions):
            return True

        return False

    def execute(self, func: Callable[[], T]) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e

                if not self.should_retry(attempt, exception=e):
                    raise

                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    time.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry logic failed without exception")


def exponential_backoff(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
):
    """
    Decorator for automatic retry with exponential backoff.

    Example:
        @exponential_backoff(max_attempts=3, backoff_factor=2.0)
        def fetch_data():
            return requests.get(url)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            strategy = RetryStrategy(
                max_attempts=max_attempts,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
                max_delay=max_delay,
                jitter=jitter,
            )
            return strategy.execute(lambda: func(*args, **kwargs))
        return wrapper
    return decorator


def with_retries(
    func: Callable[[], T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
) -> T:
    """
    Simple retry helper function.

    Example:
        result = with_retries(lambda: make_request(), max_attempts=3)
    """
    strategy = RetryStrategy(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
    )
    return strategy.execute(func)


class RetryConfig:
    """Preset retry configurations."""

    AGGRESSIVE = RetryStrategy(max_attempts=5, backoff_factor=1.5, initial_delay=0.5)
    STANDARD = RetryStrategy(max_attempts=3, backoff_factor=2.0, initial_delay=1.0)
    CONSERVATIVE = RetryStrategy(max_attempts=2, backoff_factor=3.0, initial_delay=2.0)
    NO_RETRY = RetryStrategy(max_attempts=1)
