"""Port management for Atoms MCP server."""

import socket
import threading
from typing import Optional, Set
from contextlib import contextmanager


class AtomsPortManager:
    """Manages port allocation for Atoms MCP servers."""
    
    def __init__(self):
        self._allocated_ports: Set[int] = set()
        self._lock = threading.Lock()
    
    def allocate_port(self, preferred_port: Optional[int] = None) -> int:
        """Allocate an available port."""
        with self._lock:
            if preferred_port and self._is_port_available(preferred_port):
                self._allocated_ports.add(preferred_port)
                return preferred_port
            
            # Find any available port
            for port in range(8000, 9000):
                if port not in self._allocated_ports and self._is_port_available(port):
                    self._allocated_ports.add(port)
                    return port
            
            raise RuntimeError("No available ports found")
    
    def release_port(self, port: int) -> None:
        """Release a port back to the pool."""
        with self._lock:
            self._allocated_ports.discard(port)
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False


# Global port manager instance
_port_manager = AtomsPortManager()


def get_port_manager() -> AtomsPortManager:
    """Get the global port manager instance."""
    return _port_manager


def allocate_atoms_port(preferred_port: Optional[int] = None) -> int:
    """Allocate a port for Atoms MCP server."""
    return _port_manager.allocate_port(preferred_port)


def release_atoms_port(port: int) -> None:
    """Release an Atoms MCP server port."""
    _port_manager.release_port(port)


def get_atoms_port() -> int:
    """Get the default Atoms MCP server port."""
    return allocate_atoms_port(8000)


@contextmanager
def managed_atoms_port(preferred_port: Optional[int] = None):
    """Context manager for port allocation."""
    port = allocate_atoms_port(preferred_port)
    try:
        yield port
    finally:
        release_atoms_port(port)