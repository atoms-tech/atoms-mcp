"""Bloom filter for membership testing."""

import hashlib
from typing import Any


class BloomFilter:
    """
    Bloom filter for probabilistic membership testing.

    May return false positives but never false negatives.

    Example:
        bf = BloomFilter(size=1000, num_hashes=3)
        bf.add("hello")
        bf.add("world")
        
        "hello" in bf  # True
        "goodbye" in bf  # False (probably)
    """

    def __init__(self, size: int = 1000, num_hashes: int = 3):
        """
        Initialize bloom filter.

        Args:
            size: Size of bit array
            num_hashes: Number of hash functions to use
        """
        self.size = size
        self.num_hashes = num_hashes
        self._bits = [False] * size
        self._count = 0

    def _hashes(self, item: str) -> list[int]:
        """Generate multiple hash values for item."""
        hashes = []
        
        for i in range(self.num_hashes):
            # Use different hash functions
            h = hashlib.md5(f"{item}{i}".encode()).hexdigest()
            hash_val = int(h, 16) % self.size
            hashes.append(hash_val)
        
        return hashes

    def add(self, item: Any) -> None:
        """
        Add item to bloom filter.

        Args:
            item: Item to add
        """
        item_str = str(item)
        
        for hash_val in self._hashes(item_str):
            self._bits[hash_val] = True
        
        self._count += 1

    def __contains__(self, item: Any) -> bool:
        """
        Check if item might be in filter.

        Args:
            item: Item to check

        Returns:
            True if item might be present, False if definitely not present
        """
        item_str = str(item)
        
        for hash_val in self._hashes(item_str):
            if not self._bits[hash_val]:
                return False
        
        return True

    def estimated_fp_rate(self) -> float:
        """
        Estimate false positive rate.

        Returns:
            Estimated false positive probability
        """
        if self._count == 0:
            return 0.0
        
        # (1 - e^(-k*n/m))^k
        # k = num_hashes, n = count, m = size
        import math
        exponent = -self.num_hashes * self._count / self.size
        base = 1 - math.exp(exponent)
        return base ** self.num_hashes

    def clear(self) -> None:
        """Clear all items."""
        self._bits = [False] * self.size
        self._count = 0

    def __len__(self) -> int:
        """Get approximate count of items added."""
        return self._count
