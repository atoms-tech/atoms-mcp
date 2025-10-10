"""
MCP-Specific Adapters for Provider Protocols

This module implements adapters that wrap existing MCP objects and implement
the provider protocols needed by the testing framework. Each adapter:
- Accepts existing MCP objects in __init__
- Implements all protocol methods
- Handles errors gracefully
- Includes logging for debugging
- Provides type hints and comprehensive docstrings
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from datetime import datetime

# Import existing MCP components
from fastmcp import Client
from mcp_qa.oauth.cache import CachedOAuthClient
from mcp_qa.process.monitor import ProcessMonitor, ProcessInfo, HealthStatus
from mcp_qa.utils.database_utils import DatabaseAdapter


logger = logging.getLogger(__name__)


# ============================================================================
# Protocol Definitions
# ============================================================================


class OAuthCacheProvider(Protocol):
    """Protocol for OAuth cache operations."""

    def get_cache_path(self) -> Path:
        """Get the path where OAuth tokens are cached."""
        ...

    def is_token_cached(self) -> bool:
        """Check if valid OAuth token exists in cache."""
        ...

    def clear_cache(self) -> None:
        """Clear cached OAuth token to force re-authentication."""
        ...

    async def create_client(self) -> Client:
        """Create authenticated client using cached token."""
        ...


class ClientAdapter(Protocol):
    """Protocol for MCP client communication."""

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call MCP tool and return normalized result."""
        ...

    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        ...

    async def ping(self) -> Dict[str, Any]:
        """Ping server for health check."""
        ...

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        ...


class TunnelProvider(Protocol):
    """Protocol for tunnel configuration and management."""

    def get_public_url(self) -> Optional[str]:
        """Get the public URL for the tunnel."""
        ...

    def get_local_url(self) -> str:
        """Get the local URL being tunneled."""
        ...

    def is_active(self) -> bool:
        """Check if tunnel is currently active."""
        ...

    async def start(self) -> bool:
        """Start the tunnel."""
        ...

    async def stop(self) -> bool:
        """Stop the tunnel."""
        ...


class ResourceMonitor(Protocol):
    """Protocol for resource monitoring."""

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed information about a process."""
        ...

    def find_pid_by_port(self, port: int) -> Optional[int]:
        """Find PID of process listening on a port."""
        ...

    def register_process(
        self,
        name: str,
        port: Optional[int] = None,
        pid: Optional[int] = None,
        command_pattern: Optional[str] = None
    ) -> ProcessInfo:
        """Register a process for monitoring."""
        ...

    def update_process(self, name: str) -> Optional[ProcessInfo]:
        """Update information for a registered process."""
        ...

    def check_health(self, name: str, health_url: Optional[str] = None) -> HealthStatus:
        """Check health of a process."""
        ...


class DatabaseProvider(Protocol):
    """Protocol for database operations."""

    async def query(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a query on a table."""
        ...

    async def get_single(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a single record from a table."""
        ...

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Insert one or more records."""
        ...

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Update records."""
        ...

    async def delete(self, table: str, filters: Dict[str, Any]) -> int:
        """Delete records."""
        ...


# ============================================================================
# Adapter Implementations
# ============================================================================


class MCPOAuthCacheAdapter:
    """
    Adapter for OAuth cache operations using CachedOAuthClient.

    Wraps mcp-QA OAuth cache client to implement OAuthCacheProvider protocol.

    Example:
        oauth_client = CachedOAuthClient(mcp_url="https://api.example.com/mcp")
        adapter = MCPOAuthCacheAdapter(oauth_client)

        if adapter.is_token_cached():
            client = await adapter.create_client()
        else:
            logger.info("No cached token, will perform OAuth flow")
    """

    def __init__(self, oauth_cache_client: CachedOAuthClient):
        """
        Initialize OAuth cache adapter.

        Args:
            oauth_cache_client: CachedOAuthClient instance to wrap
        """
        self._client = oauth_cache_client
        logger.debug(f"Initialized OAuth cache adapter for {oauth_cache_client.mcp_url}")

    def get_cache_path(self) -> Path:
        """
        Get the path where OAuth tokens are cached.

        Returns:
            Path to the OAuth token cache file
        """
        try:
            path = self._client._get_cache_path()
            logger.debug(f"OAuth cache path: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to get cache path: {e}")
            raise

    def is_token_cached(self) -> bool:
        """
        Check if valid OAuth token exists in cache.

        Returns:
            True if cached token exists, False otherwise
        """
        try:
            cached = self._client.is_token_cached()
            logger.debug(f"Token cached: {cached}")
            return cached
        except Exception as e:
            logger.warning(f"Error checking token cache: {e}")
            return False

    def clear_cache(self) -> None:
        """
        Clear cached OAuth token to force re-authentication.

        This will remove the cached token file, forcing a new OAuth flow
        on the next client creation.
        """
        try:
            self._client.clear_cache()
            logger.info("OAuth cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear OAuth cache: {e}")
            raise

    async def create_client(self) -> Client:
        """
        Create authenticated client using cached token.

        If no cached token exists, this will trigger the OAuth flow
        (either browser-based or Playwright automation).

        Returns:
            Authenticated FastMCP Client instance

        Raises:
            Exception: If client creation fails
        """
        try:
            logger.info("Creating OAuth client...")
            client = await self._client.create_client()
            logger.info("OAuth client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create OAuth client: {e}")
            raise


class MCPClientAdapter:
    """
    Adapter for MCP client communication.

    Wraps the existing MCPClientAdapter from core.adapters to implement
    the ClientAdapter protocol.

    Example:
        from mcp_qa.core.adapters import MCPClientAdapter as CoreAdapter

        core_adapter = CoreAdapter(client, debug=True)
        adapter = MCPClientAdapter(core_adapter)

        result = await adapter.call_tool("get_organization", {"slug": "test-org"})
    """

    def __init__(self, client_adapter):
        """
        Initialize MCP client adapter.

        Args:
            client_adapter: Core MCPClientAdapter instance to wrap
        """
        self._adapter = client_adapter
        logger.debug(f"Initialized client adapter for endpoint: {client_adapter.endpoint}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call MCP tool and return normalized result.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments/parameters

        Returns:
            Normalized result dictionary with keys:
                - success: bool
                - result: Any (tool response)
                - duration_ms: float
                - error: Optional[str]

        Raises:
            Exception: If tool call fails critically
        """
        try:
            logger.debug(f"Calling tool: {tool_name}")
            result = await self._adapter.call_tool(tool_name, arguments)

            if not result.get("success"):
                logger.warning(f"Tool call failed: {tool_name} - {result.get('error')}")

            return result
        except Exception as e:
            logger.error(f"Exception during tool call {tool_name}: {e}")
            return {
                "success": False,
                "result": None,
                "duration_ms": 0.0,
                "error": str(e),
            }

    async def list_tools(self) -> Dict[str, Any]:
        """
        List available MCP tools.

        Returns:
            Dictionary with keys:
                - success: bool
                - tools: List[Tool]
                - duration_ms: float
                - error: Optional[str]
        """
        try:
            logger.debug("Listing available tools")
            result = await self._adapter.list_tools()

            if result.get("success"):
                tool_count = len(result.get("tools", []))
                logger.info(f"Found {tool_count} available tools")

            return result
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return {
                "success": False,
                "tools": [],
                "duration_ms": 0.0,
                "error": str(e),
            }

    async def ping(self) -> Dict[str, Any]:
        """
        Ping server for health check.

        Returns:
            Dictionary with keys:
                - success: bool
                - latency_ms: float
                - error: Optional[str]
        """
        try:
            result = await self._adapter.ping()

            if result.get("success"):
                logger.debug(f"Server ping successful: {result.get('latency_ms')}ms")
            else:
                logger.warning(f"Server ping failed: {result.get('error')}")

            return result
        except Exception as e:
            logger.error(f"Exception during ping: {e}")
            return {
                "success": False,
                "latency_ms": 0.0,
                "error": str(e),
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get adapter statistics.

        Returns:
            Dictionary with keys:
                - total_calls: int
                - total_duration_ms: float
                - avg_duration_ms: float
                - endpoint: str
        """
        try:
            stats = self._adapter.get_stats()
            logger.debug(f"Client stats: {stats['total_calls']} calls, "
                        f"avg {stats['avg_duration_ms']:.2f}ms")
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_calls": 0,
                "total_duration_ms": 0.0,
                "avg_duration_ms": 0.0,
                "endpoint": "unknown",
            }


class MCPTunnelAdapter:
    """
    Adapter for tunnel configuration and management.

    Provides a simple interface for managing tunnels (ngrok, cloudflared, etc.)
    for exposing local MCP servers publicly during testing.

    Example:
        config = {
            "type": "ngrok",
            "local_url": "http://localhost:8000",
            "public_url": None  # Will be set when tunnel starts
        }
        adapter = MCPTunnelAdapter(config)

        if await adapter.start():
            print(f"Tunnel active: {adapter.get_public_url()}")
    """

    def __init__(self, tunnel_config: Dict[str, Any]):
        """
        Initialize tunnel adapter.

        Args:
            tunnel_config: Tunnel configuration dictionary with keys:
                - type: str (e.g., "ngrok", "cloudflared", "manual")
                - local_url: str (local endpoint to tunnel)
                - public_url: Optional[str] (public URL if already known)
                - auth_token: Optional[str] (for ngrok, etc.)
        """
        self._config = tunnel_config
        self._active = False
        self._public_url = tunnel_config.get("public_url")
        logger.debug(f"Initialized tunnel adapter: {tunnel_config.get('type', 'unknown')}")

    def get_public_url(self) -> Optional[str]:
        """
        Get the public URL for the tunnel.

        Returns:
            Public URL if tunnel is active, None otherwise
        """
        return self._public_url if self._active else None

    def get_local_url(self) -> str:
        """
        Get the local URL being tunneled.

        Returns:
            Local URL string
        """
        return self._config.get("local_url", "http://localhost:8000")

    def is_active(self) -> bool:
        """
        Check if tunnel is currently active.

        Returns:
            True if tunnel is active, False otherwise
        """
        return self._active

    async def start(self) -> bool:
        """
        Start the tunnel.

        This is a placeholder implementation. In a real scenario, this would:
        - Launch the tunnel process (ngrok, cloudflared)
        - Wait for tunnel to establish
        - Extract the public URL
        - Set _active = True

        Returns:
            True if tunnel started successfully, False otherwise
        """
        try:
            tunnel_type = self._config.get("type", "manual")
            logger.info(f"Starting {tunnel_type} tunnel...")

            # For manual/testing mode, just use provided public URL
            if tunnel_type == "manual":
                self._active = True
                logger.info(f"Manual tunnel mode: using {self._public_url or 'local URL'}")
                return True

            # TODO: Implement actual tunnel launching for ngrok, cloudflared, etc.
            logger.warning(f"Tunnel type '{tunnel_type}' not implemented - using manual mode")
            self._active = True
            return True

        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            return False

    async def stop(self) -> bool:
        """
        Stop the tunnel.

        This is a placeholder implementation. In a real scenario, this would:
        - Terminate the tunnel process
        - Clean up resources
        - Set _active = False

        Returns:
            True if tunnel stopped successfully, False otherwise
        """
        try:
            if not self._active:
                logger.debug("Tunnel already stopped")
                return True

            logger.info("Stopping tunnel...")
            self._active = False
            logger.info("Tunnel stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop tunnel: {e}")
            return False


class MCPResourceAdapter:
    """
    Adapter for resource monitoring operations.

    Wraps the ProcessMonitor from mcp_qa.process.monitor to implement
    the ResourceMonitor protocol.

    Example:
        monitor = ProcessMonitor()
        adapter = MCPResourceAdapter(monitor)

        # Register server process
        info = adapter.register_process("mcp-server", port=8000)

        # Check health
        health = adapter.check_health("mcp-server")
    """

    def __init__(self, process_monitor: ProcessMonitor):
        """
        Initialize resource monitor adapter.

        Args:
            process_monitor: ProcessMonitor instance to wrap
        """
        self._monitor = process_monitor
        logger.debug("Initialized resource monitor adapter")

    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed information about a process.

        Args:
            pid: Process ID

        Returns:
            ProcessInfo if process exists, None otherwise
        """
        try:
            info = self._monitor.get_process_info(pid)
            if info:
                logger.debug(f"Found process info for PID {pid}: {info.name}")
            else:
                logger.debug(f"No process found for PID {pid}")
            return info
        except Exception as e:
            logger.error(f"Error getting process info for PID {pid}: {e}")
            return None

    def find_pid_by_port(self, port: int) -> Optional[int]:
        """
        Find PID of process listening on a port.

        Args:
            port: Port number

        Returns:
            PID if found, None otherwise
        """
        try:
            pid = self._monitor.find_pid_by_port(port)
            if pid:
                logger.debug(f"Found PID {pid} listening on port {port}")
            else:
                logger.debug(f"No process found on port {port}")
            return pid
        except Exception as e:
            logger.error(f"Error finding PID for port {port}: {e}")
            return None

    def register_process(
        self,
        name: str,
        port: Optional[int] = None,
        pid: Optional[int] = None,
        command_pattern: Optional[str] = None
    ) -> ProcessInfo:
        """
        Register a process for monitoring.

        Args:
            name: Display name for process
            port: Port to check (will find PID automatically)
            pid: Known PID
            command_pattern: Pattern to find PID by command

        Returns:
            ProcessInfo object
        """
        try:
            info = self._monitor.register_process(name, port, pid, command_pattern)
            logger.info(f"Registered process: {name} (PID: {info.pid or 'unknown'})")
            return info
        except Exception as e:
            logger.error(f"Failed to register process {name}: {e}")
            raise

    def update_process(self, name: str) -> Optional[ProcessInfo]:
        """
        Update information for a registered process.

        Args:
            name: Process name

        Returns:
            Updated ProcessInfo, or None if not found
        """
        try:
            info = self._monitor.update_process(name)
            if info:
                logger.debug(f"Updated process: {name}")
            else:
                logger.warning(f"Process not found: {name}")
            return info
        except Exception as e:
            logger.error(f"Error updating process {name}: {e}")
            return None

    def check_health(self, name: str, health_url: Optional[str] = None) -> HealthStatus:
        """
        Check health of a process.

        Args:
            name: Process name
            health_url: Optional URL to check health endpoint

        Returns:
            HealthStatus enum value
        """
        try:
            health = self._monitor.check_health(name, health_url)
            logger.debug(f"Health check for {name}: {health.value}")
            return health
        except Exception as e:
            logger.error(f"Error checking health for {name}: {e}")
            from mcp_qa.process.monitor import HealthStatus
            return HealthStatus.UNKNOWN


class MCPDatabaseAdapter:
    """
    Adapter for database operations.

    Wraps a DatabaseAdapter instance to implement the DatabaseProvider protocol.

    Example:
        from mcp_qa.utils.database_utils import SupabaseDatabaseAdapter

        db_adapter = SupabaseDatabaseAdapter()
        db_adapter.set_access_token(user_token)

        adapter = MCPDatabaseAdapter(db_adapter)

        # Query users
        users = await adapter.query("users", filters={"active": True}, limit=10)
    """

    def __init__(self, database_adapter: DatabaseAdapter):
        """
        Initialize database adapter.

        Args:
            database_adapter: DatabaseAdapter instance to wrap
        """
        self._adapter = database_adapter
        logger.debug("Initialized database adapter")

    def set_access_token(self, token: str):
        """
        Set user access token for RLS context.

        Args:
            token: User's JWT access token
        """
        try:
            self._adapter.set_access_token(token)
            logger.debug("Access token set for RLS context")
        except Exception as e:
            logger.error(f"Failed to set access token: {e}")
            raise

    async def query(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query on a table.

        Args:
            table: Table name
            select: Columns to select (default: "*")
            filters: Filter conditions
            order_by: Order by clause (e.g., "created_at:desc")
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of records as dictionaries
        """
        try:
            logger.debug(f"Querying table: {table}")
            results = await self._adapter.query(
                table,
                select=select,
                filters=filters,
                order_by=order_by,
                limit=limit,
                offset=offset,
            )
            logger.debug(f"Query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Query failed on table {table}: {e}")
            raise

    async def get_single(
        self,
        table: str,
        *,
        select: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single record from a table.

        Args:
            table: Table name
            select: Columns to select (default: "*")
            filters: Filter conditions

        Returns:
            Single record as dictionary, or None if not found
        """
        try:
            logger.debug(f"Getting single record from table: {table}")
            result = await self._adapter.get_single(table, select=select, filters=filters)
            if result:
                logger.debug(f"Found record in {table}")
            else:
                logger.debug(f"No record found in {table}")
            return result
        except Exception as e:
            logger.error(f"Get single failed on table {table}: {e}")
            raise

    async def insert(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Insert one or more records.

        Args:
            table: Table name
            data: Record(s) to insert
            returning: Columns to return (default: all)

        Returns:
            Inserted record(s)
        """
        try:
            record_count = len(data) if isinstance(data, list) else 1
            logger.debug(f"Inserting {record_count} record(s) into {table}")
            result = await self._adapter.insert(table, data, returning=returning)
            logger.info(f"Successfully inserted into {table}")
            return result
        except Exception as e:
            logger.error(f"Insert failed on table {table}: {e}")
            raise

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        *,
        returning: Optional[str] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Update records.

        Args:
            table: Table name
            data: Data to update
            filters: Filter conditions for which records to update
            returning: Columns to return (default: all)

        Returns:
            Updated record(s)
        """
        try:
            logger.debug(f"Updating records in {table}")
            result = await self._adapter.update(table, data, filters, returning=returning)
            logger.info(f"Successfully updated records in {table}")
            return result
        except Exception as e:
            logger.error(f"Update failed on table {table}: {e}")
            raise

    async def delete(self, table: str, filters: Dict[str, Any]) -> int:
        """
        Delete records.

        Args:
            table: Table name
            filters: Filter conditions for which records to delete

        Returns:
            Number of deleted records
        """
        try:
            logger.debug(f"Deleting records from {table}")
            count = await self._adapter.delete(table, filters)
            logger.info(f"Deleted {count} record(s) from {table}")
            return count
        except Exception as e:
            logger.error(f"Delete failed on table {table}: {e}")
            raise


# ============================================================================
# Adapter Factory Functions
# ============================================================================


def create_oauth_adapter(mcp_url: str, **kwargs) -> MCPOAuthCacheAdapter:
    """
    Create an OAuth cache adapter for the given MCP URL.

    Args:
        mcp_url: MCP server endpoint URL
        **kwargs: Additional arguments for CachedOAuthClient

    Returns:
        MCPOAuthCacheAdapter instance

    Example:
        adapter = create_oauth_adapter("https://api.example.com/mcp")
        client = await adapter.create_client()
    """
    oauth_client = CachedOAuthClient(mcp_url, **kwargs)
    return MCPOAuthCacheAdapter(oauth_client)


def create_resource_adapter() -> MCPResourceAdapter:
    """
    Create a resource monitor adapter.

    Returns:
        MCPResourceAdapter instance

    Example:
        adapter = create_resource_adapter()
        adapter.register_process("server", port=8000)
    """
    monitor = ProcessMonitor()
    return MCPResourceAdapter(monitor)


def create_tunnel_adapter(
    tunnel_type: str = "manual",
    local_url: str = "http://localhost:8000",
    public_url: Optional[str] = None,
    **kwargs
) -> MCPTunnelAdapter:
    """
    Create a tunnel adapter.

    Args:
        tunnel_type: Type of tunnel (manual, ngrok, cloudflared)
        local_url: Local URL to tunnel
        public_url: Public URL (for manual mode)
        **kwargs: Additional tunnel configuration

    Returns:
        MCPTunnelAdapter instance

    Example:
        adapter = create_tunnel_adapter(
            tunnel_type="ngrok",
            local_url="http://localhost:8000"
        )
        await adapter.start()
    """
    config = {
        "type": tunnel_type,
        "local_url": local_url,
        "public_url": public_url,
        **kwargs
    }
    return MCPTunnelAdapter(config)


__all__ = [
    # Protocols
    "OAuthCacheProvider",
    "ClientAdapter",
    "TunnelProvider",
    "ResourceMonitor",
    "DatabaseProvider",
    # Adapters
    "MCPOAuthCacheAdapter",
    "MCPClientAdapter",
    "MCPTunnelAdapter",
    "MCPResourceAdapter",
    "MCPDatabaseAdapter",
    # Factory functions
    "create_oauth_adapter",
    "create_resource_adapter",
    "create_tunnel_adapter",
]
