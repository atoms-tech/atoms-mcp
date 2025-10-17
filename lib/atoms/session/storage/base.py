"""
Storage Backend Base

Abstract storage interface for session management with implementations
for Vercel KV, Redis, and in-memory storage.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..models import (
    Session,
    TokenRefreshRecord,
    AuditLog,
)
from ..revocation import RevocationRecord


logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    Defines interface for storing and retrieving sessions, tokens,
    revocation records, and audit logs.
    """

    @abstractmethod
    async def save_session(self, session: Session):
        """
        Save or update a session.

        Args:
            session: Session to save
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str):
        """
        Delete a session.

        Args:
            session_id: Session identifier
        """
        pass

    @abstractmethod
    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        Get all sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of sessions
        """
        pass

    @abstractmethod
    async def get_all_sessions(self, limit: int = 100) -> List[Session]:
        """
        Get all sessions (for cleanup).

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of sessions
        """
        pass

    @abstractmethod
    async def save_refresh_record(self, record: TokenRefreshRecord):
        """
        Save token refresh record.

        Args:
            record: Refresh record to save
        """
        pass

    @abstractmethod
    async def get_refresh_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[TokenRefreshRecord]:
        """
        Get refresh history for session.

        Args:
            session_id: Session identifier
            limit: Maximum number of records

        Returns:
            List of refresh records
        """
        pass

    @abstractmethod
    async def save_revocation_record(self, record: RevocationRecord):
        """
        Save revocation record.

        Args:
            record: Revocation record to save
        """
        pass

    @abstractmethod
    async def get_revocation_record(
        self,
        token_hash: str,
    ) -> Optional[RevocationRecord]:
        """
        Get revocation record by token hash.

        Args:
            token_hash: Token hash

        Returns:
            Revocation record if found
        """
        pass

    @abstractmethod
    async def get_session_revocations(
        self,
        session_id: str,
    ) -> List[RevocationRecord]:
        """
        Get all revocations for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of revocation records
        """
        pass

    @abstractmethod
    async def cleanup_expired_revocations(
        self,
        batch_size: int = 100,
    ) -> int:
        """
        Clean up expired revocation records.

        Args:
            batch_size: Number of records to process

        Returns:
            Number of records cleaned up
        """
        pass

    @abstractmethod
    async def save_audit_log(self, log: AuditLog):
        """
        Save audit log entry.

        Args:
            log: Audit log to save
        """
        pass

    @abstractmethod
    async def get_audit_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs with optional filtering.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            limit: Maximum number of logs

        Returns:
            List of audit logs
        """
        pass

    @abstractmethod
    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Get audit logs for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of logs

        Returns:
            List of audit logs
        """
        pass

    @abstractmethod
    async def close(self):
        """Close storage connections and cleanup resources."""
        pass


class InMemoryStorage(StorageBackend):
    """
    In-memory storage backend for testing and development.

    Not recommended for production use as all data is lost on restart.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, List[str]] = {}
        self._refresh_records: Dict[str, List[TokenRefreshRecord]] = {}
        self._revocations: Dict[str, RevocationRecord] = {}
        self._session_revocations: Dict[str, List[str]] = {}
        self._audit_logs: List[AuditLog] = []
        self._user_audit_logs: Dict[str, List[str]] = {}

        logger.info("Initialized in-memory storage backend")

    async def save_session(self, session: Session):
        """Save session to memory."""
        self._sessions[session.session_id] = session

        # Update user sessions index
        if session.user_id not in self._user_sessions:
            self._user_sessions[session.user_id] = []
        if session.session_id not in self._user_sessions[session.user_id]:
            self._user_sessions[session.user_id].append(session.session_id)

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session from memory."""
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str):
        """Delete session from memory."""
        session = self._sessions.pop(session_id, None)
        if session:
            user_sessions = self._user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for user from memory."""
        session_ids = self._user_sessions.get(user_id, [])
        return [
            self._sessions[sid]
            for sid in session_ids
            if sid in self._sessions
        ]

    async def get_all_sessions(self, limit: int = 100) -> List[Session]:
        """Get all sessions from memory."""
        return list(self._sessions.values())[:limit]

    async def save_refresh_record(self, record: TokenRefreshRecord):
        """Save refresh record to memory."""
        if record.session_id not in self._refresh_records:
            self._refresh_records[record.session_id] = []
        self._refresh_records[record.session_id].append(record)

    async def get_refresh_history(
        self,
        session_id: str,
        limit: int = 10,
    ) -> List[TokenRefreshRecord]:
        """Get refresh history from memory."""
        records = self._refresh_records.get(session_id, [])
        return sorted(
            records,
            key=lambda r: r.refreshed_at,
            reverse=True,
        )[:limit]

    async def save_revocation_record(self, record: RevocationRecord):
        """Save revocation record to memory."""
        self._revocations[record.token_hash] = record

        # Update session revocations index
        if record.session_id:
            if record.session_id not in self._session_revocations:
                self._session_revocations[record.session_id] = []
            self._session_revocations[record.session_id].append(record.token_hash)

    async def get_revocation_record(
        self,
        token_hash: str,
    ) -> Optional[RevocationRecord]:
        """Get revocation record from memory."""
        return self._revocations.get(token_hash)

    async def get_session_revocations(
        self,
        session_id: str,
    ) -> List[RevocationRecord]:
        """Get session revocations from memory."""
        token_hashes = self._session_revocations.get(session_id, [])
        return [
            self._revocations[th]
            for th in token_hashes
            if th in self._revocations
        ]

    async def cleanup_expired_revocations(
        self,
        batch_size: int = 100,
    ) -> int:
        """Clean up expired revocations from memory."""
        now = datetime.utcnow()
        expired = []

        for token_hash, record in self._revocations.items():
            if record.expires_at and now > record.expires_at:
                expired.append(token_hash)

        for token_hash in expired:
            record = self._revocations.pop(token_hash)
            # Clean up session index
            if record.session_id and record.session_id in self._session_revocations:
                if token_hash in self._session_revocations[record.session_id]:
                    self._session_revocations[record.session_id].remove(token_hash)

        return len(expired)

    async def save_audit_log(self, log: AuditLog):
        """Save audit log to memory."""
        self._audit_logs.append(log)

        # Update user audit logs index
        if log.user_id:
            if log.user_id not in self._user_audit_logs:
                self._user_audit_logs[log.user_id] = []
            self._user_audit_logs[log.user_id].append(log.log_id)

    async def get_audit_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs from memory."""
        logs = self._audit_logs

        if session_id:
            logs = [log for log in logs if log.session_id == session_id]
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        return sorted(
            logs,
            key=lambda l: l.timestamp,
            reverse=True,
        )[:limit]

    async def get_user_audit_logs(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get user audit logs from memory."""
        log_ids = self._user_audit_logs.get(user_id, [])
        logs = [
            log for log in self._audit_logs
            if log.log_id in log_ids
        ]
        return sorted(
            logs,
            key=lambda l: l.timestamp,
            reverse=True,
        )[:limit]

    async def close(self):
        """Close storage (no-op for in-memory)."""
        pass
