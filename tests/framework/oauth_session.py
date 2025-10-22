"""
OAuth Session Management

Provides OAuth session handling for test authentication.
"""

from typing import Any, Dict, Optional, Union
import asyncio
import time


class OAuthSessionBroker:
    """Manages OAuth sessions for test authentication."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """Initialize OAuth session broker.
        
        Args:
            base_url: Base URL for the MCP server
        """
        self.base_url = base_url
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_lock = asyncio.Lock()
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get an existing OAuth session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session data if found, None otherwise
        """
        async with self._session_lock:
            return self._sessions.get(session_id)
    
    async def create_session(self, session_id: str, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new OAuth session.
        
        Args:
            session_id: The session identifier
            auth_data: Authentication data
            
        Returns:
            Created session data
        """
        session_data = {
            "id": session_id,
            "auth_data": auth_data,
            "created_at": time.time(),
            "expires_at": time.time() + 3600,  # 1 hour default
            "active": True
        }
        
        async with self._session_lock:
            self._sessions[session_id] = session_data
        
        return session_data
    
    async def refresh_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Refresh an existing OAuth session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Refreshed session data if successful, None otherwise
        """
        async with self._session_lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            
            # Extend expiration time
            session["expires_at"] = time.time() + 3600
            session["last_refreshed"] = time.time()
            
            return session
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate an OAuth session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session was invalidated, False if not found
        """
        async with self._session_lock:
            if session_id in self._sessions:
                self._sessions[session_id]["active"] = False
                del self._sessions[session_id]
                return True
            return False
    
    async def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid and not expired.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session is valid and active
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        return (
            session.get("active", False) and 
            session.get("expires_at", 0) > time.time()
        )
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_sessions = []
        
        async with self._session_lock:
            for session_id, session in self._sessions.items():
                if session.get("expires_at", 0) <= current_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self._sessions[session_id]
        
        return len(expired_sessions)
    
    async def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions.
        
        Returns:
            Dictionary of all active sessions
        """
        async with self._session_lock:
            return {k: v for k, v in self._sessions.items() if v.get("active", False)}


# Global session broker instance
_global_session_broker: Optional[OAuthSessionBroker] = None


def get_session_broker() -> OAuthSessionBroker:
    """Get the global session broker instance.
    
    Returns:
        Global OAuth session broker
    """
    global _global_session_broker
    if _global_session_broker is None:
        _global_session_broker = OAuthSessionBroker()
    return _global_session_broker


def set_session_broker(broker: OAuthSessionBroker) -> None:
    """Set the global session broker instance.
    
    Args:
        broker: The session broker to use globally
    """
    global _global_session_broker
    _global_session_broker = broker