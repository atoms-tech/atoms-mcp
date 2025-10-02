"""Session manager for stateless OAuth with Supabase persistence.

Enables stateless serverless MCP deployments by persisting OAuth sessions
in Supabase between requests.
"""

from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from supabase import Client

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage MCP OAuth sessions in Supabase."""

    def __init__(self, supabase_client: Client, session_ttl_hours: int = 24):
        """Initialize session manager.

        Args:
            supabase_client: Supabase client instance (with service role or anon key)
            session_ttl_hours: Session time-to-live in hours (default: 24)
        """
        self.client = supabase_client
        self.session_ttl_hours = session_ttl_hours

    async def create_session(
        self,
        user_id: str,
        oauth_data: Dict[str, Any],
        mcp_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new session and return session_id.

        Args:
            user_id: User identifier from OAuth (will be cast to UUID if needed)
            oauth_data: OAuth tokens and user info to persist
            mcp_state: Optional MCP connection state

        Returns:
            session_id: Generated session identifier
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(datetime.now().astimezone().tzinfo) + timedelta(hours=self.session_ttl_hours)

        try:
            # Ensure user_id is valid UUID format
            # If it's not, we'll use it as-is and let Supabase handle it
            insert_data = {
                "session_id": session_id,
                "user_id": user_id,  # Supabase will cast to UUID
                "oauth_data": oauth_data,
                "mcp_state": mcp_state or {},
                "expires_at": expires_at.isoformat(),
            }

            result = self.client.table("mcp_sessions").insert(insert_data).execute()

            logger.info(f"✅ Created session {session_id} for user {user_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            logger.error(f"Insert data was: {insert_data}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data by session_id.

        Args:
            session_id: Session identifier

        Returns:
            Session data dict or None if not found/expired
        """
        try:
            result = self.client.table("mcp_sessions").select("*").eq(
                "session_id", session_id
            ).execute()

            if not result.data or len(result.data) == 0:
                logger.warning(f"Session {session_id} not found")
                return None

            session = result.data[0]

            # Check expiry
            expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
            now = datetime.now(expires_at.tzinfo)
            if expires_at < now:
                logger.warning(f"Session {session_id} expired")
                await self.delete_session(session_id)
                return None

            logger.debug(f"✅ Retrieved session {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        oauth_data: Optional[Dict[str, Any]] = None,
        mcp_state: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            oauth_data: Updated OAuth data (optional)
            mcp_state: Updated MCP state (optional)

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            update_data: Dict[str, Any] = {"updated_at": datetime.now().isoformat()}

            if oauth_data is not None:
                update_data["oauth_data"] = oauth_data
            if mcp_state is not None:
                update_data["mcp_state"] = mcp_state

            result = self.client.table("mcp_sessions").update(update_data).eq(
                "session_id", session_id
            ).execute()

            if result.data and len(result.data) > 0:
                logger.debug(f"✅ Updated session {session_id}")
                return True
            else:
                logger.warning(f"Session {session_id} not found for update")
                return False

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.client.table("mcp_sessions").delete().eq(
                "session_id", session_id
            ).execute()

            logger.info(f"✅ Deleted session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions.

        Returns:
            Number of sessions deleted
        """
        try:
            result = self.client.table("mcp_sessions").delete().lt(
                "expires_at", datetime.now().isoformat()
            ).execute()

            count = len(result.data) if result.data else 0
            logger.info(f"✅ Cleaned up {count} expired sessions")
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def extend_session(self, session_id: str, hours: Optional[int] = None) -> bool:
        """Extend session expiry time.

        Args:
            session_id: Session identifier
            hours: Hours to extend (default: use session_ttl_hours)

        Returns:
            True if extended successfully, False otherwise
        """
        try:
            extension_hours = hours or self.session_ttl_hours
            new_expires_at = datetime.now() + timedelta(hours=extension_hours)

            result = self.client.table("mcp_sessions").update({
                "expires_at": new_expires_at.isoformat(),
                "updated_at": datetime.now().isoformat(),
            }).eq("session_id", session_id).execute()

            if result.data and len(result.data) > 0:
                logger.debug(f"✅ Extended session {session_id} by {extension_hours}h")
                return True
            else:
                logger.warning(f"Session {session_id} not found for extension")
                return False

        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False


def create_session_manager(access_token: Optional[str] = None) -> SessionManager:
    """Factory function to create a SessionManager with Supabase client.

    Args:
        access_token: Optional access token for user context

    Returns:
        Configured SessionManager instance
    """
    from supabase_client import get_supabase

    # Get Supabase client - use service role if available for session management
    # Otherwise fall back to anon key (requires RLS policies on mcp_sessions)
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if service_role_key:
        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        from supabase import create_client
        client = create_client(url, service_role_key)
        logger.debug("Using service role key for session management")
    else:
        client = get_supabase(access_token)
        logger.debug("Using anon key for session management (ensure RLS policies allow)")

    session_ttl = int(os.getenv("MCP_SESSION_TTL_HOURS", "24"))
    return SessionManager(client, session_ttl_hours=session_ttl)
