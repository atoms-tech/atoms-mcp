"""Retry policy for webhook delivery."""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RetryPolicy:
    """
    Retry policy with exponential backoff.
    
    Example:
        policy = RetryPolicy(max_attempts=3, initial_delay=60)
        next_retry = policy.next_retry_time(attempt=1)
    """
    
    max_attempts: int = 3
    initial_delay: int = 60  # seconds
    multiplier: float = 2.0
    max_delay: int = 3600  # 1 hour
    
    def next_retry_time(self, attempt: int) -> datetime:
        """
        Calculate next retry time using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Next retry datetime
        """
        delay = min(
            self.initial_delay * (self.multiplier ** attempt),
            self.max_delay
        )
        return datetime.utcnow() + timedelta(seconds=delay)
