"""
Parallel Client Management

Provides parallel client management for concurrent test execution.
"""

from typing import Any, Dict, List, Optional, Union
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelClientManager:
    """Manages multiple MCP clients for parallel test execution."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize parallel client manager.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self._clients: Dict[str, Any] = {}
        self._client_lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def add_client(self, client_id: str, client: Any) -> None:
        """Add a client to the manager.
        
        Args:
            client_id: Unique identifier for the client
            client: The MCP client instance
        """
        async with self._client_lock:
            self._clients[client_id] = {
                "client": client,
                "created_at": time.time(),
                "last_used": time.time(),
                "active": True
            }
    
    async def get_client(self, client_id: str) -> Optional[Any]:
        """Get a client by ID.
        
        Args:
            client_id: The client identifier
            
        Returns:
            Client instance if found, None otherwise
        """
        async with self._client_lock:
            client_data = self._clients.get(client_id)
            if client_data and client_data.get("active", False):
                client_data["last_used"] = time.time()
                return client_data["client"]
            return None
    
    async def remove_client(self, client_id: str) -> bool:
        """Remove a client from the manager.
        
        Args:
            client_id: The client identifier
            
        Returns:
            True if client was removed, False if not found
        """
        async with self._client_lock:
            if client_id in self._clients:
                self._clients[client_id]["active"] = False
                del self._clients[client_id]
                return True
            return False
    
    async def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute tasks in parallel across available clients.
        
        Args:
            tasks: List of task dictionaries with 'client_id', 'method', and 'args' keys
            
        Returns:
            List of task results in the same order as input tasks
        """
        if not tasks:
            return []
        
        # Group tasks by client
        client_tasks = {}
        for i, task in enumerate(tasks):
            client_id = task.get("client_id", "default")
            if client_id not in client_tasks:
                client_tasks[client_id] = []
            client_tasks[client_id].append((i, task))
        
        # Execute tasks in parallel
        results = [None] * len(tasks)
        
        async def execute_client_tasks(client_id: str, client_task_list: List[tuple]) -> None:
            client = await self.get_client(client_id)
            if not client:
                # If client not found, mark all tasks as failed
                for task_index, _ in client_task_list:
                    results[task_index] = {"error": f"Client {client_id} not found"}
                return
            
            for task_index, task in client_task_list:
                try:
                    method_name = task.get("method")
                    args = task.get("args", [])
                    kwargs = task.get("kwargs", {})
                    
                    if hasattr(client, method_name):
                        method = getattr(client, method_name)
                        if asyncio.iscoroutinefunction(method):
                            result = await method(*args, **kwargs)
                        else:
                            result = method(*args, **kwargs)
                        results[task_index] = result
                    else:
                        results[task_index] = {"error": f"Method {method_name} not found on client"}
                except Exception as e:
                    results[task_index] = {"error": str(e)}
        
        # Create tasks for each client
        client_coroutines = [
            execute_client_tasks(client_id, client_task_list)
            for client_id, client_task_list in client_tasks.items()
        ]
        
        # Execute all client tasks concurrently
        await asyncio.gather(*client_coroutines, return_exceptions=True)
        
        return results
    
    async def execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Execute tasks sequentially using available clients.
        
        Args:
            tasks: List of task dictionaries with 'client_id', 'method', and 'args' keys
            
        Returns:
            List of task results in the same order as input tasks
        """
        results = []
        
        for task in tasks:
            client_id = task.get("client_id", "default")
            client = await self.get_client(client_id)
            
            if not client:
                results.append({"error": f"Client {client_id} not found"})
                continue
            
            try:
                method_name = task.get("method")
                args = task.get("args", [])
                kwargs = task.get("kwargs", {})
                
                if hasattr(client, method_name):
                    method = getattr(client, method_name)
                    if asyncio.iscoroutinefunction(method):
                        result = await method(*args, **kwargs)
                    else:
                        result = method(*args, **kwargs)
                    results.append(result)
                else:
                    results.append({"error": f"Method {method_name} not found on client"})
            except Exception as e:
                results.append({"error": str(e)})
        
        return results
    
    async def get_client_stats(self) -> Dict[str, Any]:
        """Get statistics about managed clients.
        
        Returns:
            Dictionary with client statistics
        """
        async with self._client_lock:
            active_clients = sum(1 for client_data in self._clients.values() if client_data.get("active", False))
            total_clients = len(self._clients)
            
            return {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "max_workers": self.max_workers,
                "clients": {
                    client_id: {
                        "created_at": client_data["created_at"],
                        "last_used": client_data["last_used"],
                        "active": client_data["active"]
                    }
                    for client_id, client_data in self._clients.items()
                }
            }
    
    async def cleanup_inactive_clients(self, max_age_seconds: int = 3600) -> int:
        """Clean up inactive clients older than specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds before cleanup
            
        Returns:
            Number of clients cleaned up
        """
        current_time = time.time()
        clients_to_remove = []
        
        async with self._client_lock:
            for client_id, client_data in self._clients.items():
                if (not client_data.get("active", False) or 
                    current_time - client_data.get("last_used", 0) > max_age_seconds):
                    clients_to_remove.append(client_id)
            
            for client_id in clients_to_remove:
                del self._clients[client_id]
        
        return len(clients_to_remove)
    
    async def close(self) -> None:
        """Close the parallel client manager and cleanup resources."""
        async with self._client_lock:
            self._clients.clear()
        
        self._executor.shutdown(wait=True)


# Global parallel client manager instance
_global_parallel_manager: Optional[ParallelClientManager] = None


def get_parallel_manager() -> ParallelClientManager:
    """Get the global parallel client manager instance.
    
    Returns:
        Global parallel client manager
    """
    global _global_parallel_manager
    if _global_parallel_manager is None:
        _global_parallel_manager = ParallelClientManager()
    return _global_parallel_manager


def set_parallel_manager(manager: ParallelClientManager) -> None:
    """Set the global parallel client manager instance.
    
    Args:
        manager: The parallel client manager to use globally
    """
    global _global_parallel_manager
    _global_parallel_manager = manager