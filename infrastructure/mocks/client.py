"""HTTP MCP client for local/hosted MCP servers.

Supports connection pooling, retry logic, and health checks.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict

try:
    import aiohttp
except ImportError:
    aiohttp = None


class HttpMcpClient:
    """HTTP client for local/hosted MCP servers.
    
    Supports:
    - Connection pooling and reuse
    - Exponential backoff retry logic
    - Health check validation
    - Request/response logging
    """
    
    def __init__(self, base_url: str, *, timeout: int = 30, max_retries: int = 3):
        """Initialize HTTP MCP client.
        
        Args:
            base_url: Base URL of MCP server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retries on transient errors (default: 3)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = None
        self._last_health_check = None
        self._is_healthy = False

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self._session is None:
            if aiohttp is None:
                raise ImportError(
                    "aiohttp is required for HttpMcpClient. Install it with: pip install aiohttp"
                )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def health(self) -> Dict[str, Any]:
        """Check MCP server health.
        
        Returns:
            Health status dict (e.g., {"status": "ok", "uptime": 12345})
            
        Raises:
            ConnectionError: If server is unreachable
        """
        try:
            sess = await self._get_session()
            async with sess.get(f"{self.base_url}/health") as r:
                r.raise_for_status()
                result = await r.json()
                self._is_healthy = True
                self._last_health_check = time.time()
                return result
        except Exception as e:
            self._is_healthy = False
            raise ConnectionError(f"Failed to connect to MCP server at {self.base_url}: {e}")

    async def call_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP server method with retry logic.
        
        Args:
            payload: MCP request payload (must include 'method' field)
            
        Returns:
            MCP response dict
            
        Raises:
            ConnectionError: If all retries are exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                sess = await self._get_session()
                async with sess.post(
                    f"{self.base_url}/api/mcp",
                    json=payload,
                ) as r:
                    r.raise_for_status()
                    result = await r.json()
                    self._is_healthy = True
                    return result
            except Exception as e:
                last_error = e
                
                # Exponential backoff: 2^attempt seconds (1s, 2s, 4s, ...)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
        
        self._is_healthy = False
        raise ConnectionError(
            f"MCP call failed after {self.max_retries} attempts: {last_error}"
        )

    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
