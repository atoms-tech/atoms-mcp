"""Search result types for Vector-Kit."""

from __future__ import annotations

from typing import List, Dict, Any, Optional, NamedTuple
from datetime import datetime


class SearchResult(NamedTuple):
    """Single search result with similarity score."""
    id: str
    entity_type: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchResponse:
    """Response containing multiple search results."""
    
    def __init__(
        self,
        results: List[SearchResult],
        query: str,
        search_type: str,
        total_results: int,
        execution_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.results = results
        self.query = query
        self.search_type = search_type
        self.total_results = total_results
        self.execution_time_ms = execution_time_ms
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return (
            f"SearchResponse(query='{self.query}', "
            f"search_type='{self.search_type}', "
            f"results={len(self.results)}/{self.total_results}, "
            f"time={self.execution_time_ms:.2f}ms)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r._asdict() for r in self.results],
            "query": self.query,
            "search_type": self.search_type,
            "total_results": self.total_results,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata
        }
