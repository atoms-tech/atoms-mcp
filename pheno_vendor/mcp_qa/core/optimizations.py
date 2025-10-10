"""
Performance Optimizations for MCP Test Suite

This module provides optimized client adapters with connection pooling,
batching, caching, and concurrency management for improved test performance.
"""

import asyncio
import hashlib
import json
from utils.logging_setup import get_logger
import multiprocessing
import os
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from threading import Lock
import httpx

logger = get_logger(__name__)


class OptimizationFlags:
    """Configuration flags for enabling/disabling optimizations."""

    def __init__(
        self,
        enable_connection_pooling: bool = True,
        enable_batch_requests: bool = True,
        enable_concurrency_optimization: bool = True,
        enable_response_caching: bool = True,
        enable_network_optimization: bool = True,
        pool_min_size: int = 4,
        pool_max_size: int = 20,
        batch_size: int = 10,
        cache_max_entries: int = 1000,
        cache_ttl_seconds: int = 60,
        worker_multiplier: int = 2,
        enable_http2: bool = True,
        enable_compression: bool = True,
        connection_timeout: int = 30,
        request_timeout: int = 60,
    ):
        self.enable_connection_pooling = enable_connection_pooling
        self.enable_batch_requests = enable_batch_requests
        self.enable_concurrency_optimization = enable_concurrency_optimization
        self.enable_response_caching = enable_response_caching
        self.enable_network_optimization = enable_network_optimization
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        self.batch_size = batch_size
        self.cache_max_entries = cache_max_entries
        self.cache_ttl_seconds = cache_ttl_seconds
        self.worker_multiplier = worker_multiplier
        self.enable_http2 = enable_http2
        self.enable_compression = enable_compression
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout

    @classmethod
    def from_env(cls) -> "OptimizationFlags":
        """Create flags from environment variables."""
        return cls(
            enable_connection_pooling=os.getenv("MCP_ENABLE_POOLING", "true").lower() == "true",
            enable_batch_requests=os.getenv("MCP_ENABLE_BATCHING", "true").lower() == "true",
            enable_concurrency_optimization=os.getenv("MCP_ENABLE_CONCURRENCY", "true").lower() == "true",
            enable_response_caching=os.getenv("MCP_ENABLE_CACHING", "true").lower() == "true",
            enable_network_optimization=os.getenv("MCP_ENABLE_NETWORK_OPT", "true").lower() == "true",
            pool_min_size=int(os.getenv("MCP_POOL_MIN_SIZE", "4")),
            pool_max_size=int(os.getenv("MCP_POOL_MAX_SIZE", "20")),
            batch_size=int(os.getenv("MCP_BATCH_SIZE", "10")),
            cache_max_entries=int(os.getenv("MCP_CACHE_MAX_ENTRIES", "1000")),
            cache_ttl_seconds=int(os.getenv("MCP_CACHE_TTL", "60")),
            worker_multiplier=int(os.getenv("MCP_WORKER_MULTIPLIER", "2")),
            enable_http2=os.getenv("MCP_ENABLE_HTTP2", "true").lower() == "true",
            enable_compression=os.getenv("MCP_ENABLE_COMPRESSION", "true").lower() == "true",
            connection_timeout=int(os.getenv("MCP_CONNECTION_TIMEOUT", "30")),
            request_timeout=int(os.getenv("MCP_REQUEST_TIMEOUT", "60")),
        )


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""
    value: Any
    timestamp: float
    ttl: int

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class ResponseCacheLayer:
    """LRU cache for MCP responses with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(self, method: str, params: Dict[str, Any]) -> str:
        """Generate cache key from method and parameters."""
        key_data = json.dumps({"method": method, "params": params}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        key = self._generate_key(method, params)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    logger.debug(f"Cache hit for {method}")
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]

            self._misses += 1
            return None

    def set(self, method: str, params: Dict[str, Any], value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with TTL."""
        key = self._generate_key(method, params)
        ttl = ttl or self.default_ttl

        with self._lock:
            # Remove oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "entries": len(self._cache),
                "max_size": self.max_size,
            }


@dataclass
class ConnectionStats:
    """Statistics for connection pool."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    reconnections: int = 0
    total_requests: int = 0


class PooledConnection:
    """A single pooled connection with health checking."""

    def __init__(self, connection_id: int, timeout: int = 30):
        self.connection_id = connection_id
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.created_at = time.time()
        self.last_used = time.time()
        self.is_healthy = True
        self.request_count = 0

    async def connect(self, base_url: str, http2: bool = True) -> None:
        """Establish connection."""
        try:
            self.client = httpx.AsyncClient(
                base_url=base_url,
                timeout=self.timeout,
                http2=http2,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
            self.is_healthy = True
            logger.debug(f"Connection {self.connection_id} established")
        except Exception as e:
            self.is_healthy = False
            logger.error(f"Failed to establish connection {self.connection_id}: {e}")
            raise

    async def close(self) -> None:
        """Close connection."""
        if self.client:
            await self.client.aclose()
            self.client = None
        logger.debug(f"Connection {self.connection_id} closed")

    async def health_check(self) -> bool:
        """Perform health check on connection."""
        if not self.client:
            self.is_healthy = False
            return False

        try:
            # Simple health check - could be customized
            self.is_healthy = True
            return True
        except Exception as e:
            logger.warning(f"Health check failed for connection {self.connection_id}: {e}")
            self.is_healthy = False
            return False

    async def execute_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Execute a request using this connection."""
        if not self.client or not self.is_healthy:
            raise RuntimeError(f"Connection {self.connection_id} is not healthy")

        try:
            self.last_used = time.time()
            self.request_count += 1

            if method.upper() == "GET":
                response = await self.client.get(endpoint, **kwargs)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.is_healthy = False
            logger.error(f"Request failed on connection {self.connection_id}: {e}")
            raise


class PooledMCPClient:
    """MCP Client with connection pooling and automatic reconnection."""

    def __init__(
        self,
        base_url: str,
        min_connections: int = 4,
        max_connections: int = 20,
        connection_timeout: int = 30,
        enable_http2: bool = True,
    ):
        self.base_url = base_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.enable_http2 = enable_http2

        self._pool: List[PooledConnection] = []
        self._available: asyncio.Queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_connections)
        self._stats = ConnectionStats()
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize connection pool with minimum connections."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            logger.info(f"Initializing connection pool (min: {self.min_connections}, max: {self.max_connections})")

            for i in range(self.min_connections):
                conn = await self._create_connection(i)
                self._pool.append(conn)
                await self._available.put(conn)

            self._stats.total_connections = len(self._pool)
            self._stats.idle_connections = len(self._pool)
            self._initialized = True
            logger.info("Connection pool initialized")

    async def _create_connection(self, conn_id: int) -> PooledConnection:
        """Create a new pooled connection."""
        conn = PooledConnection(conn_id, timeout=self.connection_timeout)
        try:
            await conn.connect(self.base_url, http2=self.enable_http2)
            return conn
        except Exception as e:
            self._stats.failed_connections += 1
            logger.error(f"Failed to create connection: {e}")
            raise

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self._initialized:
            await self.initialize()

        async with self._semaphore:
            # Try to get available connection
            try:
                conn = await asyncio.wait_for(self._available.get(), timeout=5.0)
            except asyncio.TimeoutError:
                # Create new connection if under max limit
                if len(self._pool) < self.max_connections:
                    conn_id = len(self._pool)
                    conn = await self._create_connection(conn_id)
                    self._pool.append(conn)
                    self._stats.total_connections += 1
                else:
                    # Wait for available connection
                    conn = await self._available.get()

            self._stats.active_connections += 1
            self._stats.idle_connections -= 1

            # Health check and reconnect if needed
            if not await conn.health_check():
                try:
                    await conn.close()
                    await conn.connect(self.base_url, http2=self.enable_http2)
                    self._stats.reconnections += 1
                except Exception as e:
                    logger.error(f"Failed to reconnect: {e}")
                    raise

            try:
                yield conn
            finally:
                self._stats.active_connections -= 1
                self._stats.idle_connections += 1
                await self._available.put(conn)

    async def execute(self, method: str, endpoint: str, **kwargs) -> Any:
        """Execute a request using pooled connection."""
        async with self.acquire() as conn:
            self._stats.total_requests += 1
            return await conn.execute_request(method, endpoint, **kwargs)

    async def close(self) -> None:
        """Close all connections in the pool."""
        logger.info("Closing connection pool")
        for conn in self._pool:
            await conn.close()
        self._pool.clear()
        self._initialized = False

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "total_connections": self._stats.total_connections,
            "active_connections": self._stats.active_connections,
            "idle_connections": self._stats.idle_connections,
            "failed_connections": self._stats.failed_connections,
            "reconnections": self._stats.reconnections,
            "total_requests": self._stats.total_requests,
        }


@dataclass
class BatchRequest:
    """A single request in a batch."""
    request_id: str
    method: str
    endpoint: str
    params: Dict[str, Any]
    future: asyncio.Future


class BatchRequestOptimizer:
    """Optimizer for batching multiple requests together."""

    def __init__(
        self,
        client: PooledMCPClient,
        batch_size: int = 10,
        batch_timeout: float = 0.1,
    ):
        self.client = client
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending: List[BatchRequest] = []
        self._lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        self._request_hashes: Dict[str, List[asyncio.Future]] = {}

    def _generate_request_hash(self, method: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate hash for request deduplication."""
        key_data = json.dumps({"method": method, "endpoint": endpoint, "params": params}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def add_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Add a request to the batch queue."""
        params = params or {}
        request_hash = self._generate_request_hash(method, endpoint, params)

        async with self._lock:
            # Check for duplicate requests
            if request_hash in self._request_hashes:
                # Deduplicate: wait for existing request
                logger.debug(f"Deduplicating request: {method} {endpoint}")
                future = asyncio.Future()
                self._request_hashes[request_hash].append(future)
                return await future

            # Create new request
            request_id = f"req_{len(self._pending)}_{time.time()}"
            future = asyncio.Future()

            request = BatchRequest(
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                params=params,
                future=future,
            )

            self._pending.append(request)
            self._request_hashes[request_hash] = [future]

            # Start batch processing if needed
            if len(self._pending) >= self.batch_size:
                await self._process_batch()
            elif not self._batch_task or self._batch_task.done():
                self._batch_task = asyncio.create_task(self._batch_timeout_handler())

        return await future

    async def _batch_timeout_handler(self) -> None:
        """Process batch after timeout if not full."""
        await asyncio.sleep(self.batch_timeout)
        async with self._lock:
            if self._pending:
                await self._process_batch()

    async def _process_batch(self) -> None:
        """Process all pending requests in parallel."""
        if not self._pending:
            return

        batch = self._pending[:]
        self._pending.clear()
        self._request_hashes.clear()

        logger.debug(f"Processing batch of {len(batch)} requests")

        # Process requests in parallel
        tasks = [
            self._execute_request(req)
            for req in batch
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_request(self, request: BatchRequest) -> None:
        """Execute a single request and set its future."""
        try:
            result = await self.client.execute(
                request.method,
                request.endpoint,
                json=request.params,
            )
            request.future.set_result(result)
        except Exception as e:
            request.future.set_exception(e)

    async def flush(self) -> None:
        """Flush all pending requests immediately."""
        async with self._lock:
            if self._pending:
                await self._process_batch()


class ConcurrencyOptimizer:
    """Optimizer for managing concurrent test execution."""

    def __init__(
        self,
        worker_multiplier: int = 2,
        max_workers: Optional[int] = None,
        memory_limit_gb: float = 4.0,
    ):
        self.worker_multiplier = worker_multiplier
        self.memory_limit_gb = memory_limit_gb
        self._max_workers = max_workers
        self._rate_limiter: Optional[asyncio.Semaphore] = None

    def get_optimal_worker_count(self) -> int:
        """Calculate optimal worker count based on CPU and memory."""
        if self._max_workers:
            return self._max_workers

        # Base on CPU cores
        cpu_count = multiprocessing.cpu_count()
        optimal = cpu_count * self.worker_multiplier

        # Adjust for memory constraints
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024 ** 3)
            memory_based_workers = int(available_memory_gb / 0.5)  # Assume 500MB per worker
            optimal = min(optimal, memory_based_workers)
        except ImportError:
            logger.warning("psutil not available, skipping memory-based worker adjustment")

        logger.info(f"Optimal worker count: {optimal} (CPU cores: {cpu_count})")
        return max(1, optimal)

    def create_rate_limiter(self, max_concurrent: Optional[int] = None) -> asyncio.Semaphore:
        """Create a rate limiter for concurrent operations."""
        if max_concurrent is None:
            max_concurrent = self.get_optimal_worker_count()

        self._rate_limiter = asyncio.Semaphore(max_concurrent)
        return self._rate_limiter

    @asynccontextmanager
    async def limit_concurrency(self):
        """Context manager for limiting concurrency."""
        if not self._rate_limiter:
            self._rate_limiter = self.create_rate_limiter()

        async with self._rate_limiter:
            yield


class NetworkOptimizer:
    """Network-level optimizations for HTTP requests."""

    @staticmethod
    def create_optimized_client(
        base_url: str,
        enable_http2: bool = True,
        enable_compression: bool = True,
        timeout: int = 30,
    ) -> httpx.AsyncClient:
        """Create an optimized HTTP client with advanced features."""
        headers = {}
        if enable_compression:
            headers["Accept-Encoding"] = "gzip, deflate, br"

        return httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            http2=enable_http2,
            headers=headers,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            ),
            transport=httpx.AsyncHTTPTransport(
                retries=3,
                http2=enable_http2,
            ),
        )


class OptimizedMCPClient:
    """
    Fully optimized MCP client with all optimization layers.

    This is the main client that applications should use.
    """

    def __init__(
        self,
        base_url: str,
        flags: Optional[OptimizationFlags] = None,
    ):
        self.base_url = base_url
        self.flags = flags or OptimizationFlags()

        # Initialize optimization layers
        self._pooled_client: Optional[PooledMCPClient] = None
        self._batch_optimizer: Optional[BatchRequestOptimizer] = None
        self._concurrency_optimizer: Optional[ConcurrencyOptimizer] = None
        self._cache: Optional[ResponseCacheLayer] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all optimization layers."""
        if self._initialized:
            return

        logger.info("Initializing optimized MCP client")

        # Connection pooling
        if self.flags.enable_connection_pooling:
            self._pooled_client = PooledMCPClient(
                base_url=self.base_url,
                min_connections=self.flags.pool_min_size,
                max_connections=self.flags.pool_max_size,
                connection_timeout=self.flags.connection_timeout,
                enable_http2=self.flags.enable_http2,
            )
            await self._pooled_client.initialize()

        # Batch optimizer
        if self.flags.enable_batch_requests and self._pooled_client:
            self._batch_optimizer = BatchRequestOptimizer(
                client=self._pooled_client,
                batch_size=self.flags.batch_size,
            )

        # Concurrency optimizer
        if self.flags.enable_concurrency_optimization:
            self._concurrency_optimizer = ConcurrencyOptimizer(
                worker_multiplier=self.flags.worker_multiplier,
            )

        # Response cache
        if self.flags.enable_response_caching:
            self._cache = ResponseCacheLayer(
                max_size=self.flags.cache_max_entries,
                default_ttl=self.flags.cache_ttl_seconds,
            )

        self._initialized = True
        logger.info("Optimized MCP client initialized")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        use_cache: bool = True,
    ) -> Any:
        """
        Call an MCP tool with all optimizations applied.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            use_cache: Whether to use response cache

        Returns:
            Tool response
        """
        if not self._initialized:
            await self.initialize()

        # Check cache first
        if use_cache and self._cache:
            cached = self._cache.get(tool_name, arguments)
            if cached is not None:
                return cached

        # Execute request
        if self._batch_optimizer:
            result = await self._batch_optimizer.add_request(
                method="POST",
                endpoint="/tools/call",
                params={"tool": tool_name, "arguments": arguments},
            )
        elif self._pooled_client:
            result = await self._pooled_client.execute(
                method="POST",
                endpoint="/tools/call",
                json={"tool": tool_name, "arguments": arguments},
            )
        else:
            # Fallback to direct request
            client = NetworkOptimizer.create_optimized_client(
                base_url=self.base_url,
                enable_http2=self.flags.enable_http2,
                enable_compression=self.flags.enable_compression,
            )
            try:
                response = await client.post(
                    "/tools/call",
                    json={"tool": tool_name, "arguments": arguments},
                )
                response.raise_for_status()
                result = response.json()
            finally:
                await client.aclose()

        # Cache result for read-only operations
        if use_cache and self._cache and self._is_read_only(tool_name):
            self._cache.set(tool_name, arguments, result)

        return result

    def _is_read_only(self, tool_name: str) -> bool:
        """Check if a tool is read-only (safe to cache)."""
        read_only_prefixes = ["get_", "list_", "search_", "query_", "find_"]
        return any(tool_name.startswith(prefix) for prefix in read_only_prefixes)

    async def close(self) -> None:
        """Close all resources."""
        if self._batch_optimizer:
            await self._batch_optimizer.flush()

        if self._pooled_client:
            await self._pooled_client.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all optimization layers."""
        stats = {}

        if self._pooled_client:
            stats["connection_pool"] = self._pooled_client.get_stats()

        if self._cache:
            stats["cache"] = self._cache.get_stats()

        if self._concurrency_optimizer:
            stats["concurrency"] = {
                "optimal_workers": self._concurrency_optimizer.get_optimal_worker_count(),
            }

        return stats


# Convenience function for creating optimized client
def create_optimized_client(
    base_url: str,
    **kwargs
) -> OptimizedMCPClient:
    """
    Create an optimized MCP client with default settings.

    Args:
        base_url: Base URL for MCP server
        **kwargs: Additional flags for OptimizationFlags

    Returns:
        Optimized MCP client
    """
    flags = OptimizationFlags(**kwargs)
    return OptimizedMCPClient(base_url, flags)


# Export public API
__all__ = [
    "OptimizationFlags",
    "PooledMCPClient",
    "BatchRequestOptimizer",
    "ConcurrencyOptimizer",
    "ResponseCacheLayer",
    "NetworkOptimizer",
    "OptimizedMCPClient",
    "create_optimized_client",
]
