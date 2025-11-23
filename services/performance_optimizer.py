"""Performance Optimizer for Atoms MCP - Query optimization and caching.

Provides query optimization, intelligent caching, batch processing,
and performance monitoring.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Engine for optimizing query performance."""

    def __init__(self, cache_ttl_seconds: int = 300):
        """Initialize performance optimizer.
        
        Args:
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.cache_ttl = cache_ttl_seconds
        self.query_cache = {}
        self.cache_stats = defaultdict(lambda: {"hits": 0, "misses": 0})
        self.query_metrics = []
        self.batch_queue = []

    def optimize_query(
        self,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize a query for performance.
        
        Args:
            query: Query dict
            
        Returns:
            Optimized query dict
        """
        optimized = query.copy()

        # Add query hints
        optimized["hints"] = self._generate_query_hints(query)

        # Suggest indexes
        optimized["suggested_indexes"] = self._suggest_indexes(query)

        # Estimate cost
        optimized["estimated_cost"] = self._estimate_query_cost(query)

        return optimized

    def cache_query_result(
        self,
        query_key: str,
        result: Any
    ) -> None:
        """Cache query result.
        
        Args:
            query_key: Query key
            result: Query result
        """
        self.query_cache[query_key] = {
            "result": result,
            "timestamp": datetime.now(),
            "ttl": self.cache_ttl
        }

    def get_cached_result(
        self,
        query_key: str
    ) -> Optional[Any]:
        """Get cached query result.
        
        Args:
            query_key: Query key
            
        Returns:
            Cached result or None
        """
        if query_key not in self.query_cache:
            self.cache_stats[query_key]["misses"] += 1
            return None

        cached = self.query_cache[query_key]
        age = (datetime.now() - cached["timestamp"]).total_seconds()

        if age > cached["ttl"]:
            del self.query_cache[query_key]
            self.cache_stats[query_key]["misses"] += 1
            return None

        self.cache_stats[query_key]["hits"] += 1
        return cached["result"]

    def batch_process(
        self,
        queries: List[Dict[str, Any]]
    ) -> List[Any]:
        """Process queries in batch.
        
        Args:
            queries: List of queries
            
        Returns:
            List of results
        """
        results = []

        for query in queries:
            # Simulate batch processing
            result = {
                "query_id": query.get("id"),
                "status": "processed",
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)

        return results

    def track_query_performance(
        self,
        query_id: str,
        execution_time_ms: float,
        result_count: int
    ) -> Dict[str, Any]:
        """Track query performance metrics.
        
        Args:
            query_id: Query ID
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results
            
        Returns:
            Performance metric record
        """
        metric = {
            "query_id": query_id,
            "execution_time_ms": execution_time_ms,
            "result_count": result_count,
            "timestamp": datetime.now().isoformat(),
            "performance_level": self._calculate_performance_level(execution_time_ms)
        }

        self.query_metrics.append(metric)
        return metric

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report.
        
        Returns:
            Performance report
        """
        if not self.query_metrics:
            return {
                "total_queries": 0,
                "average_execution_time_ms": 0,
                "cache_hit_rate": 0
            }

        total_queries = len(self.query_metrics)
        avg_time = sum(m["execution_time_ms"] for m in self.query_metrics) / total_queries
        total_results = sum(m["result_count"] for m in self.query_metrics)

        total_hits = sum(stats["hits"] for stats in self.cache_stats.values())
        total_misses = sum(stats["misses"] for stats in self.cache_stats.values())
        total_requests = total_hits + total_misses

        cache_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_queries": total_queries,
            "average_execution_time_ms": avg_time,
            "total_results": total_results,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": total_hits,
            "cache_misses": total_misses,
            "report_timestamp": datetime.now().isoformat()
        }

    def identify_slow_queries(
        self,
        threshold_ms: float = 100.0
    ) -> List[Dict[str, Any]]:
        """Identify slow queries.
        
        Args:
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of slow queries
        """
        slow_queries = [
            m for m in self.query_metrics
            if m["execution_time_ms"] > threshold_ms
        ]

        return sorted(slow_queries, key=lambda x: x["execution_time_ms"], reverse=True)

    def suggest_optimizations(
        self,
        query: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest optimizations for query.
        
        Args:
            query: Query dict
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Check for missing filters
        if not query.get("filters"):
            suggestions.append({
                "type": "missing_filter",
                "description": "Add filters to reduce result set",
                "priority": "high"
            })

        # Check for missing indexes
        if query.get("entity_type") and not query.get("indexed"):
            suggestions.append({
                "type": "missing_index",
                "description": f"Create index on {query.get('entity_type')}",
                "priority": "high"
            })

        # Check for pagination
        if not query.get("limit"):
            suggestions.append({
                "type": "missing_pagination",
                "description": "Add pagination to limit results",
                "priority": "medium"
            })

        return suggestions

    def _generate_query_hints(self, query: Dict[str, Any]) -> List[str]:
        """Generate query hints.
        
        Args:
            query: Query dict
            
        Returns:
            List of hints
        """
        hints = []

        if query.get("filters"):
            hints.append("use_index")

        if query.get("limit"):
            hints.append("early_termination")

        if query.get("sort"):
            hints.append("use_sort_index")

        return hints

    def _suggest_indexes(self, query: Dict[str, Any]) -> List[str]:
        """Suggest indexes for query.
        
        Args:
            query: Query dict
            
        Returns:
            List of suggested indexes
        """
        indexes = []

        if query.get("entity_type"):
            indexes.append(f"idx_{query['entity_type']}")

        if query.get("filters"):
            for filter_key in query["filters"].keys():
                indexes.append(f"idx_{filter_key}")

        return indexes

    def _estimate_query_cost(self, query: Dict[str, Any]) -> float:
        """Estimate query cost.
        
        Args:
            query: Query dict
            
        Returns:
            Estimated cost
        """
        cost = 1.0

        if not query.get("filters"):
            cost *= 10.0

        if query.get("limit"):
            cost *= 0.5

        if query.get("indexed"):
            cost *= 0.1

        return cost

    def _calculate_performance_level(self, execution_time_ms: float) -> str:
        """Calculate performance level.
        
        Args:
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Performance level
        """
        if execution_time_ms < 10:
            return "excellent"
        elif execution_time_ms < 50:
            return "good"
        elif execution_time_ms < 100:
            return "fair"
        elif execution_time_ms < 500:
            return "poor"
        else:
            return "critical"


# Global performance optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer

