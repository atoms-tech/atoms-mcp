"""Circular buffer implementation."""

from typing import Any, Iterator, List, Optional


class CircularBuffer:
    """
    Fixed-size circular buffer (ring buffer).

    Example:
        buffer = CircularBuffer(capacity=3)
        buffer.append(1)
        buffer.append(2)
        buffer.append(3)
        buffer.append(4)  # Overwrites oldest item (1)
        
        list(buffer)  # [2, 3, 4]
    """

    def __init__(self, capacity: int):
        """
        Initialize circular buffer.

        Args:
            capacity: Maximum buffer size
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self.capacity = capacity
        self._buffer: List[Optional[Any]] = [None] * capacity
        self._head = 0  # Write position
        self._size = 0  # Current size

    def append(self, item: Any) -> None:
        """
        Append item to buffer.

        Args:
            item: Item to append
        """
        self._buffer[self._head] = item
        self._head = (self._head + 1) % self.capacity
        
        if self._size < self.capacity:
            self._size += 1

    def get(self, index: int) -> Any:
        """
        Get item at index.

        Args:
            index: Index (0 = oldest item)

        Returns:
            Item at index
        """
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        
        # Calculate actual position
        if self._size < self.capacity:
            actual_index = index
        else:
            actual_index = (self._head + index) % self.capacity
        
        return self._buffer[actual_index]

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self._size == self.capacity

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self._size == 0

    def size(self) -> int:
        """Get current buffer size."""
        return self._size

    def clear(self) -> None:
        """Clear buffer."""
        self._buffer = [None] * self.capacity
        self._head = 0
        self._size = 0

    def to_list(self) -> List[Any]:
        """Convert buffer to list (oldest to newest)."""
        if self._size == 0:
            return []
        
        if self._size < self.capacity:
            return self._buffer[:self._size]
        else:
            # Rearrange from oldest to newest
            return self._buffer[self._head:] + self._buffer[:self._head]

    def __len__(self) -> int:
        """Get buffer size."""
        return self._size

    def __iter__(self) -> Iterator[Any]:
        """Iterate over buffer (oldest to newest)."""
        return iter(self.to_list())

    def __repr__(self) -> str:
        """String representation."""
        return f"CircularBuffer({self.to_list()})"
