"""Memory optimization utilities for handling large contexts efficiently.

This module provides:
- Context compression and chunking strategies
- Memory-efficient text processing
- Intelligent context window management
- Memory leak detection and prevention
- Garbage collection optimization
- Large file handling with streaming
"""

import gc
import gzip
import hashlib
import logging
import mmap
import os
import threading
import time
import zlib
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    # Process memory
    rss_mb: float = 0.0  # Resident Set Size
    vms_mb: float = 0.0  # Virtual Memory Size
    percent: float = 0.0  # Memory percentage

    # System memory
    total_mb: float = 0.0
    available_mb: float = 0.0
    used_mb: float = 0.0

    # GC stats
    gc_collections: dict[int, int] = field(default_factory=dict)
    gc_collected: dict[int, int] = field(default_factory=dict)
    gc_uncollectable: dict[int, int] = field(default_factory=dict)

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompressionResult:
    """Result of text compression operation."""

    compressed_data: bytes
    original_size: int
    compressed_size: int
    compression_ratio: float
    encoding: str = "utf-8"
    algorithm: str = "gzip"

    def decompress(self) -> str:
        """Decompress the data back to original string."""
        if self.algorithm == "gzip":
            return gzip.decompress(self.compressed_data).decode(self.encoding)
        elif self.algorithm == "zlib":
            return zlib.decompress(self.compressed_data).decode(self.encoding)
        else:
            raise ValueError(f"Unsupported compression algorithm: {self.algorithm}")


class MemoryMonitor:
    """Monitor memory usage and detect issues."""

    def __init__(self, warning_threshold_mb: float = 1000.0, critical_threshold_mb: float = 2000.0):
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.process = psutil.Process()
        self.memory_history: deque = deque(maxlen=100)
        self._lock = threading.RLock()

    def get_current_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        try:
            # Process memory
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # System memory
            system_memory = psutil.virtual_memory()

            # GC stats
            gc_stats = {}
            collected_stats = {}
            uncollectable_stats = {}

            for generation in range(3):
                stats = gc.get_stats()[generation] if gc.get_stats() else {}
                gc_stats[generation] = stats.get("collections", 0)
                collected_stats[generation] = stats.get("collected", 0)
                uncollectable_stats[generation] = stats.get("uncollectable", 0)

            stats = MemoryStats(
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                total_mb=system_memory.total / 1024 / 1024,
                available_mb=system_memory.available / 1024 / 1024,
                used_mb=system_memory.used / 1024 / 1024,
                gc_collections=gc_stats,
                gc_collected=collected_stats,
                gc_uncollectable=uncollectable_stats,
            )

            with self._lock:
                self.memory_history.append(stats)

            return stats

        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")
            return MemoryStats()

    def check_memory_pressure(self) -> dict[str, Any]:
        """Check if system is under memory pressure."""
        stats = self.get_current_memory_stats()

        status = "normal"
        recommendations = []

        if stats.rss_mb > self.critical_threshold_mb:
            status = "critical"
            recommendations.extend(
                [
                    "Immediate garbage collection required",
                    "Consider reducing context window size",
                    "Clear unnecessary caches",
                ]
            )
        elif stats.rss_mb > self.warning_threshold_mb:
            status = "warning"
            recommendations.extend(
                ["Monitor memory usage closely", "Consider enabling compression", "Run garbage collection"]
            )

        # Check for memory growth trend
        if len(self.memory_history) >= 5:
            recent_memory = [s.rss_mb for s in list(self.memory_history)[-5:]]
            if recent_memory[-1] > recent_memory[0] * 1.5:  # 50% growth
                status = max(status, "growing", key=lambda x: ["normal", "growing", "warning", "critical"].index(x))
                recommendations.append("Memory usage is growing rapidly")

        return {
            "status": status,
            "current_memory_mb": stats.rss_mb,
            "system_available_mb": stats.available_mb,
            "memory_percent": stats.percent,
            "recommendations": recommendations,
            "thresholds": {"warning_mb": self.warning_threshold_mb, "critical_mb": self.critical_threshold_mb},
        }

    def suggest_optimizations(self) -> list[str]:
        """Suggest memory optimizations based on current state."""
        stats = self.get_current_memory_stats()
        suggestions = []

        # Check GC effectiveness
        total_collections = sum(stats.gc_collections.values())
        total_collected = sum(stats.gc_collected.values())

        if total_collections > 0 and total_collected / total_collections < 0.1:
            suggestions.append("Low garbage collection efficiency - check for circular references")

        if stats.gc_uncollectable[2] > 0:  # Generation 2 uncollectable objects
            suggestions.append("Uncollectable objects detected - investigate circular references")

        # Memory usage suggestions
        if stats.rss_mb > 500:
            suggestions.extend(
                [
                    "Enable text compression for large contexts",
                    "Use streaming for large file operations",
                    "Implement context chunking strategies",
                ]
            )

        if stats.percent > 80:
            suggestions.extend(
                [
                    "System memory usage is high",
                    "Consider reducing concurrent operations",
                    "Clear unused caches and buffers",
                ]
            )

        return suggestions


class TextCompressor:
    """Efficient text compression utilities."""

    @staticmethod
    def compress_text(text: str, algorithm: str = "gzip", level: int = 6) -> CompressionResult:
        """Compress text using specified algorithm."""
        if not text:
            return CompressionResult(
                compressed_data=b"", original_size=0, compressed_size=0, compression_ratio=0.0, algorithm=algorithm
            )

        text_bytes = text.encode("utf-8")
        original_size = len(text_bytes)

        if algorithm == "gzip":
            compressed_data = gzip.compress(text_bytes, compresslevel=level)
        elif algorithm == "zlib":
            compressed_data = zlib.compress(text_bytes, level)
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")

        compressed_size = len(compressed_data)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0

        return CompressionResult(
            compressed_data=compressed_data,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            algorithm=algorithm,
        )

    @staticmethod
    def should_compress(text: str, min_size: int = 1024, min_ratio: float = 1.2) -> bool:
        """Determine if text should be compressed based on size and potential ratio."""
        if len(text) < min_size:
            return False

        # Quick sample compression to estimate ratio
        sample_size = min(len(text), 1000)
        sample = text[:sample_size]
        sample_result = TextCompressor.compress_text(sample)

        return sample_result.compression_ratio >= min_ratio


class ContextManager:
    """Manage large contexts efficiently."""

    def __init__(self, max_context_tokens: int = 128000, compression_threshold: int = 10000):
        self.max_context_tokens = max_context_tokens
        self.compression_threshold = compression_threshold
        self.compressed_contexts: dict[str, CompressionResult] = {}
        self._lock = threading.RLock()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4

    def chunk_context(self, text: str, max_chunk_tokens: int = None) -> list[str]:
        """Split context into manageable chunks."""
        max_chunk_tokens = max_chunk_tokens or (self.max_context_tokens // 4)
        max_chunk_chars = max_chunk_tokens * 4  # Rough conversion

        if len(text) <= max_chunk_chars:
            return [text]

        chunks = []
        lines = text.split("\n")
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > max_chunk_chars and current_chunk:
                # Finalize current chunk
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def compress_context(self, context_id: str, text: str) -> bool:
        """Compress and store context if beneficial."""
        if len(text) < self.compression_threshold:
            return False

        if TextCompressor.should_compress(text):
            compressed = TextCompressor.compress_text(text)

            with self._lock:
                self.compressed_contexts[context_id] = compressed

            logger.debug(
                f"Compressed context {context_id}: "
                f"{compressed.original_size} -> {compressed.compressed_size} bytes "
                f"(ratio: {compressed.compression_ratio:.1f}x)"
            )
            return True

        return False

    def get_context(self, context_id: str) -> str | None:
        """Retrieve and decompress context."""
        with self._lock:
            compressed = self.compressed_contexts.get(context_id)

        if compressed:
            return compressed.decompress()

        return None

    def remove_context(self, context_id: str):
        """Remove compressed context."""
        with self._lock:
            self.compressed_contexts.pop(context_id, None)

    def get_memory_usage(self) -> dict[str, Any]:
        """Get memory usage of compressed contexts."""
        with self._lock:
            total_original = sum(c.original_size for c in self.compressed_contexts.values())
            total_compressed = sum(c.compressed_size for c in self.compressed_contexts.values())
            count = len(self.compressed_contexts)

        return {
            "contexts_count": count,
            "total_original_mb": total_original / 1024 / 1024,
            "total_compressed_mb": total_compressed / 1024 / 1024,
            "memory_saved_mb": (total_original - total_compressed) / 1024 / 1024,
            "average_compression_ratio": total_original / total_compressed if total_compressed > 0 else 0,
        }


class LargeFileHandler:
    """Handle large files efficiently with memory optimization."""

    @staticmethod
    def read_file_chunked(file_path: str, chunk_size: int = 8192) -> Generator[str, None, None]:
        """Read file in chunks to avoid memory issues."""
        try:
            with open(file_path, encoding="utf-8") as file:
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    @staticmethod
    def read_file_mmap(file_path: str) -> str:
        """Read file using memory mapping for large files."""
        try:
            with open(file_path, encoding="utf-8") as file:
                with mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    return mm.read().decode("utf-8")
        except Exception as e:
            logger.error(f"Error reading file with mmap {file_path}: {e}")
            # Fallback to regular read
            with open(file_path, encoding="utf-8") as file:
                return file.read()

    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in MB."""
        try:
            return os.path.getsize(file_path) / 1024 / 1024
        except Exception:
            return 0.0

    @staticmethod
    def should_use_streaming(file_path: str, size_threshold_mb: float = 10.0) -> bool:
        """Determine if file should be processed using streaming."""
        return LargeFileHandler.get_file_size_mb(file_path) > size_threshold_mb


class GarbageCollector:
    """Enhanced garbage collection utilities."""

    @staticmethod
    def force_gc(generation: int | None = None) -> dict[str, int]:
        """Force garbage collection and return statistics."""
        if generation is not None:
            collected = gc.collect(generation)
            return {"collected": collected, "generation": generation}
        else:
            collected = gc.collect()
            return {"collected": collected, "generation": "all"}

    @staticmethod
    def find_circular_references() -> list[Any]:
        """Find objects involved in circular references."""
        # This is a simplified implementation
        # In production, you might want more sophisticated detection

        # Force full GC first
        gc.collect()

        # Get all objects tracked by GC
        all_objects = gc.get_objects()

        # Find objects that are still alive but have references to each other
        circular_objects = []

        for obj in all_objects:
            if gc.is_tracked(obj):
                gc.get_referrers(obj)
                referents = gc.get_referents(obj)

                # Simple check for potential circular reference
                for referent in referents:
                    if obj in gc.get_referents(referent):
                        circular_objects.append(obj)
                        break

        return circular_objects

    @staticmethod
    def get_gc_stats() -> dict[str, Any]:
        """Get comprehensive garbage collection statistics."""
        stats = gc.get_stats()

        return {
            "generations": len(stats),
            "generation_stats": stats,
            "gc_counts": gc.get_count(),
            "gc_threshold": gc.get_threshold(),
            "tracked_objects": len(gc.get_objects()),
        }

    @staticmethod
    def optimize_gc_thresholds():
        """Optimize GC thresholds based on current memory usage."""
        # Get current stats
        gc.get_count()
        current_thresholds = gc.get_threshold()

        # Simple optimization: increase thresholds if we have low memory pressure
        memory_monitor = MemoryMonitor()
        pressure = memory_monitor.check_memory_pressure()

        if pressure["status"] == "normal":
            # Increase thresholds to reduce GC frequency
            new_thresholds = tuple(int(t * 1.5) for t in current_thresholds)
            gc.set_threshold(*new_thresholds)
            logger.debug(f"Increased GC thresholds: {current_thresholds} -> {new_thresholds}")
        elif pressure["status"] in ["warning", "critical"]:
            # Decrease thresholds to increase GC frequency
            new_thresholds = tuple(max(100, int(t * 0.7)) for t in current_thresholds)
            gc.set_threshold(*new_thresholds)
            logger.debug(f"Decreased GC thresholds: {current_thresholds} -> {new_thresholds}")


class MemoryOptimizer:
    """Main memory optimization coordinator."""

    def __init__(self):
        self.memory_monitor = MemoryMonitor()
        self.context_manager = ContextManager()
        self.text_compressor = TextCompressor()
        self._optimization_history: list[dict[str, Any]] = []

    def optimize_memory(self) -> dict[str, Any]:
        """Perform comprehensive memory optimization."""
        start_time = time.time()
        start_memory = self.memory_monitor.get_current_memory_stats().rss_mb

        optimizations_performed = []

        # 1. Force garbage collection
        gc_result = GarbageCollector.force_gc()
        optimizations_performed.append(f"GC collected {gc_result['collected']} objects")

        # 2. Optimize GC thresholds
        GarbageCollector.optimize_gc_thresholds()
        optimizations_performed.append("Optimized GC thresholds")

        # 3. Check for circular references
        circular_refs = GarbageCollector.find_circular_references()
        if circular_refs:
            optimizations_performed.append(f"Found {len(circular_refs)} potential circular references")

        # 4. Compress large contexts if any
        context_usage = self.context_manager.get_memory_usage()
        if context_usage["contexts_count"] > 0:
            optimizations_performed.append(f"Managing {context_usage['contexts_count']} compressed contexts")

        end_time = time.time()
        end_memory = self.memory_monitor.get_current_memory_stats().rss_mb

        memory_freed_mb = start_memory - end_memory

        result = {
            "optimizations_performed": optimizations_performed,
            "memory_freed_mb": memory_freed_mb,
            "optimization_time_ms": (end_time - start_time) * 1000,
            "memory_before_mb": start_memory,
            "memory_after_mb": end_memory,
            "gc_stats": GarbageCollector.get_gc_stats(),
            "context_usage": context_usage,
        }

        self._optimization_history.append(result)

        # Keep only recent optimization history
        if len(self._optimization_history) > 50:
            self._optimization_history = self._optimization_history[-25:]

        logger.info(
            f"Memory optimization completed: {memory_freed_mb:.1f}MB freed in {result['optimization_time_ms']:.1f}ms"
        )

        return result

    def get_optimization_recommendations(self) -> list[str]:
        """Get personalized memory optimization recommendations."""
        recommendations = []

        # Get current memory state
        pressure = self.memory_monitor.check_memory_pressure()
        recommendations.extend(pressure["recommendations"])

        # Add monitor-specific suggestions
        monitor_suggestions = self.memory_monitor.suggest_optimizations()
        recommendations.extend(monitor_suggestions)

        # Check optimization history for patterns
        if len(self._optimization_history) >= 3:
            recent_optimizations = self._optimization_history[-3:]
            avg_freed = sum(opt["memory_freed_mb"] for opt in recent_optimizations) / len(recent_optimizations)

            if avg_freed < 10:  # Less than 10MB freed on average
                recommendations.append("Recent optimizations had limited impact - consider architectural changes")

            if any(len(opt["optimizations_performed"]) > 5 for opt in recent_optimizations):
                recommendations.append("Frequent optimizations needed - investigate memory usage patterns")

        return list(set(recommendations))  # Remove duplicates

    def get_memory_health_report(self) -> dict[str, Any]:
        """Generate comprehensive memory health report."""
        current_stats = self.memory_monitor.get_current_memory_stats()
        pressure_check = self.memory_monitor.check_memory_pressure()
        context_usage = self.context_manager.get_memory_usage()
        gc_stats = GarbageCollector.get_gc_stats()
        recommendations = self.get_optimization_recommendations()

        return {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": {
                "process_memory_mb": current_stats.rss_mb,
                "system_memory_percent": current_stats.percent,
                "available_memory_mb": current_stats.available_mb,
            },
            "pressure_status": pressure_check["status"],
            "context_compression": context_usage,
            "garbage_collection": {
                "tracked_objects": gc_stats["tracked_objects"],
                "recent_collections": sum(current_stats.gc_collections.values()),
                "recent_collected": sum(current_stats.gc_collected.values()),
            },
            "optimization_history_count": len(self._optimization_history),
            "recommendations": recommendations,
            "health_score": self._calculate_health_score(current_stats, pressure_check),
        }

    def _calculate_health_score(self, stats: MemoryStats, pressure: dict[str, Any]) -> int:
        """Calculate memory health score (0-100)."""
        score = 100

        # Deduct points based on memory usage
        if stats.percent > 90:
            score -= 40
        elif stats.percent > 80:
            score -= 20
        elif stats.percent > 70:
            score -= 10

        # Deduct points based on pressure status
        if pressure["status"] == "critical":
            score -= 30
        elif pressure["status"] == "warning":
            score -= 15
        elif pressure["status"] == "growing":
            score -= 10

        # Deduct points for uncollectable objects
        uncollectable = sum(stats.gc_uncollectable.values())
        if uncollectable > 0:
            score -= min(20, uncollectable * 2)

        return max(0, score)


# Global memory optimizer instance
_memory_optimizer: MemoryOptimizer | None = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer


def optimize_memory_now() -> dict[str, Any]:
    """Perform immediate memory optimization."""
    optimizer = get_memory_optimizer()
    return optimizer.optimize_memory()


def get_memory_recommendations() -> list[str]:
    """Get current memory optimization recommendations."""
    optimizer = get_memory_optimizer()
    return optimizer.get_optimization_recommendations()


def compress_large_context(text: str, context_id: str = None) -> str | None:
    """Compress large context text if beneficial."""
    if not context_id:
        context_id = hashlib.md5(text.encode()).hexdigest()[:8]

    optimizer = get_memory_optimizer()
    if optimizer.context_manager.compress_context(context_id, text):
        return context_id

    return None


def get_compressed_context(context_id: str) -> str | None:
    """Retrieve compressed context."""
    optimizer = get_memory_optimizer()
    return optimizer.context_manager.get_context(context_id)
