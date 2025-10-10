"""Trie (prefix tree) implementation."""

from typing import List, Optional


class TrieNode:
    """Node in trie."""

    def __init__(self):
        self.children = {}
        self.is_end = False
        self.value = None


class Trie:
    """
    Trie data structure for efficient prefix-based operations.

    Example:
        trie = Trie()
        trie.insert("hello")
        trie.insert("world")
        
        trie.search("hello")  # True
        trie.starts_with("hel")  # True
        trie.find_all_with_prefix("hel")  # ["hello"]
    """

    def __init__(self):
        """Initialize trie."""
        self.root = TrieNode()
        self._size = 0

    def insert(self, word: str, value: Optional[any] = None) -> None:
        """
        Insert word into trie.

        Args:
            word: Word to insert
            value: Optional value to associate with word
        """
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        if not node.is_end:
            self._size += 1
        
        node.is_end = True
        node.value = value

    def search(self, word: str) -> bool:
        """
        Search for exact word in trie.

        Args:
            word: Word to search

        Returns:
            True if word exists
        """
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """
        Check if any word starts with prefix.

        Args:
            prefix: Prefix to search

        Returns:
            True if prefix exists
        """
        return self._find_node(prefix) is not None

    def get(self, word: str) -> Optional[any]:
        """
        Get value associated with word.

        Args:
            word: Word to look up

        Returns:
            Associated value or None
        """
        node = self._find_node(word)
        if node and node.is_end:
            return node.value
        return None

    def find_all_with_prefix(self, prefix: str) -> List[str]:
        """
        Find all words with given prefix.

        Args:
            prefix: Prefix to search

        Returns:
            List of words with prefix
        """
        node = self._find_node(prefix)
        if not node:
            return []
        
        results = []
        self._collect_words(node, prefix, results)
        return results

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Find node for given prefix."""
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node

    def _collect_words(self, node: TrieNode, prefix: str, results: List[str]) -> None:
        """Recursively collect all words from node."""
        if node.is_end:
            results.append(prefix)
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, results)

    def delete(self, word: str) -> bool:
        """
        Delete word from trie.

        Args:
            word: Word to delete

        Returns:
            True if word was deleted
        """
        def _delete_helper(node: TrieNode, word: str, index: int) -> bool:
            if index == len(word):
                if not node.is_end:
                    return False
                node.is_end = False
                return len(node.children) == 0
            
            char = word[index]
            if char not in node.children:
                return False
            
            child = node.children[char]
            should_delete = _delete_helper(child, word, index + 1)
            
            if should_delete:
                del node.children[char]
                return not node.is_end and len(node.children) == 0
            
            return False
        
        if self.search(word):
            _delete_helper(self.root, word, 0)
            self._size -= 1
            return True
        return False

    def size(self) -> int:
        """Get number of words in trie."""
        return self._size

    def __len__(self) -> int:
        """Get number of words."""
        return self._size

    def __contains__(self, word: str) -> bool:
        """Check if word exists."""
        return self.search(word)
