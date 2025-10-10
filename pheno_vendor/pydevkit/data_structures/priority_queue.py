"""Priority queue implementation."""

import heapq
from dataclasses import dataclass, field
from typing import Any, List


@dataclass(order=True)
class PriorityItem:
    """Item for priority queue."""
    priority: int
    item: Any = field(compare=False)


class PriorityQueue:
    """
    Priority queue implementation using heapq.

    Lower priority numbers = higher priority (processed first).

    Example:
        pq = PriorityQueue()
        pq.push("urgent", priority=1)
        pq.push("normal", priority=5)
        pq.push("low", priority=10)
        
        item = pq.pop()  # Returns "urgent"
    """

    def __init__(self):
        """Initialize priority queue."""
        self._heap: List[PriorityItem] = []
        self._counter = 0  # For stable sorting

    def push(self, item: Any, priority: int = 0) -> None:
        """
        Add item to queue.

        Args:
            item: Item to add
            priority: Priority (lower = higher priority)
        """
        # Use counter for stable sort (FIFO for same priority)
        heapq.heappush(self._heap, PriorityItem(priority, (self._counter, item)))
        self._counter += 1

    def pop(self) -> Any:
        """
        Remove and return highest priority item.

        Returns:
            Highest priority item

        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("pop from empty priority queue")

        priority_item = heapq.heappop(self._heap)
        _, item = priority_item.item
        return item

    def peek(self) -> Any:
        """
        Get highest priority item without removing.

        Returns:
            Highest priority item

        Raises:
            IndexError: If queue is empty
        """
        if self.is_empty():
            raise IndexError("peek from empty priority queue")

        _, item = self._heap[0].item
        return item

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._heap) == 0

    def size(self) -> int:
        """Get queue size."""
        return len(self._heap)

    def clear(self) -> None:
        """Clear all items."""
        self._heap.clear()
        self._counter = 0

    def __len__(self) -> int:
        """Get queue size."""
        return len(self._heap)

    def __bool__(self) -> bool:
        """Check if queue is non-empty."""
        return not self.is_empty()
