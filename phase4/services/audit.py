"""Audit service for tracking authentication events."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..storage import StorageBackend, get_storage_backend
from utils.logging_setup import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Session events
    SESSION_CREATED = "session.created"
    SESSION_TERMINATED = "session.terminated"
    SESSION_TOKENS_UPDATED = "session.tokens_updated"
    SESSION_IP_CHANGE = "session.ip_change"

    # Token events
    TOKEN_REFRESHED = "token.refreshed"
    TOKEN_REFRESH_FAILED = "token.refresh_failed"
    TOKEN_REVOKED = "token.revoked"
    TOKEN_ROTATION = "token.rotation"

    # Security events
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    DEVICE_MISMATCH = "security.device_mismatch"
    IP_MISMATCH = "security.ip_mismatch"

    # Access events
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.SESSION_CREATED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical


class AuditService:
    """Service for audit logging of authentication events.

    Features:
    - Structured audit logging
    - Event aggregation
    - Compliance reporting
    - Security monitoring
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
    ):
        """Initialize audit service.

        Args:
            storage: Storage backend
        """
        self.storage = storage or get_storage_backend()
        self.enable_audit = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
        self.audit_retention_days = int(os.getenv("AUDIT_RETENTION_DAYS", "90"))

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ) -> str:
        """Log an audit event.

        Args:
            event_type: Type of event
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP
            user_agent: User agent string
            details: Event details
            severity: Event severity

        Returns:
            Event ID
        """
        if not self.enable_audit:
            return ""

        import uuid

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            severity=severity,
        )

        # Store event
        await self._store_event(event)

        # Log to system logger
        logger.info(
            f"Audit: {event_type.value} - "
            f"user={user_id}, session={session_id}, "
            f"details={json.dumps(details or {})}"
        )

        return event.event_id

    async def log_session_created(
        self,
        session_id: str,
        user_id: str,
        device_info: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> str:
        """Log session creation event."""
        details = {}
        if device_info:
            details["device"] = device_info.to_dict() if hasattr(device_info, "to_dict") else str(device_info)

        return await self.log_event(
            AuditEventType.SESSION_CREATED,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
        )

    async def log_session_terminated(
        self,
        session_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> str:
        """Log session termination event."""
        return await self.log_event(
            AuditEventType.SESSION_TERMINATED,
            user_id=user_id,
            session_id=session_id,
            details={"reason": reason or "User initiated"},
        )

    async def log_session_tokens_updated(
        self,
        session_id: str,
        user_id: str,
    ) -> str:
        """Log session token update event."""
        return await self.log_event(
            AuditEventType.SESSION_TOKENS_UPDATED,
            user_id=user_id,
            session_id=session_id,
        )

    async def log_session_ip_change(
        self,
        session_id: str,
        old_ip: str,
        new_ip: str,
    ) -> str:
        """Log IP address change event."""
        return await self.log_event(
            AuditEventType.SESSION_IP_CHANGE,
            session_id=session_id,
            ip_address=new_ip,
            details={"old_ip": old_ip, "new_ip": new_ip},
            severity="warning",
        )

    async def log_token_refresh(
        self,
        session_id: Optional[str] = None,
        old_token_hash: Optional[str] = None,
        new_token_hash: Optional[str] = None,
        rotation: bool = False,
    ) -> str:
        """Log token refresh event."""
        return await self.log_event(
            AuditEventType.TOKEN_REFRESHED,
            session_id=session_id,
            details={
                "old_token_hash": old_token_hash,
                "new_token_hash": new_token_hash,
                "rotation": rotation,
            },
        )

    async def log_token_refresh_failure(
        self,
        session_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> str:
        """Log token refresh failure event."""
        return await self.log_event(
            AuditEventType.TOKEN_REFRESH_FAILED,
            session_id=session_id,
            details={"error": error},
            severity="error",
        )

    async def log_token_revoked(
        self,
        token_hash: str,
        token_type: str,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Log token revocation event."""
        return await self.log_event(
            AuditEventType.TOKEN_REVOKED,
            user_id=user_id,
            session_id=session_id,
            details={
                "token_hash": token_hash,
                "token_type": token_type,
                "reason": reason,
            },
            severity="warning",
        )

    async def log_suspicious_activity(
        self,
        session_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log suspicious activity event."""
        return await self.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            session_id=session_id,
            details={"reason": reason, **(details or {})},
            severity="critical",
        )

    async def log_rate_limit_exceeded(
        self,
        identifier: str,
        operation: str,
        limit: int,
        window: int,
    ) -> str:
        """Log rate limit exceeded event."""
        return await self.log_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            details={
                "identifier": identifier,
                "operation": operation,
                "limit": limit,
                "window_seconds": window,
            },
            severity="warning",
        )

    async def get_events(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query audit events.

        Args:
            user_id: Filter by user
            session_id: Filter by session
            event_type: Filter by event type
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum events to return

        Returns:
            List of audit events
        """
        # Build query pattern
        patterns = []

        if user_id:
            patterns.append(f"audit:user:{user_id}:*")
        elif session_id:
            patterns.append(f"audit:session:{session_id}:*")
        else:
            patterns.append("audit:*")

        events = []

        for pattern in patterns:
            keys = await self.storage.scan(pattern, count=limit * 2)

            for key in keys[:limit]:
                event_data = await self.storage.get(key)

                if event_data:
                    # Apply filters
                    if event_type and event_data.get("event_type") != event_type.value:
                        continue

                    event_time = datetime.fromisoformat(event_data["timestamp"])

                    if start_time and event_time < start_time:
                        continue

                    if end_time and event_time > end_time:
                        continue

                    events.append(event_data)

        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"], reverse=True)

        return events[:limit]

    async def get_event_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """Get event statistics.

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            Event counts by type
        """
        events = await self.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        stats = {}

        for event in events:
            event_type = event.get("event_type", "unknown")
            stats[event_type] = stats.get(event_type, 0) + 1

        return stats

    async def _store_event(self, event: AuditEvent) -> None:
        """Store audit event in backend.

        Args:
            event: Event to store
        """
        # Store by multiple keys for querying
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "session_id": event.session_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "details": event.details,
            "severity": event.severity,
        }

        # TTL for audit records
        ttl = self.audit_retention_days * 86400

        # Store by event ID
        await self.storage.set(
            f"audit:event:{event.event_id}",
            event_data,
            expire=ttl
        )

        # Index by user if present
        if event.user_id:
            await self.storage.set(
                f"audit:user:{event.user_id}:{event.event_id}",
                event_data,
                expire=ttl
            )

        # Index by session if present
        if event.session_id:
            await self.storage.set(
                f"audit:session:{event.session_id}:{event.event_id}",
                event_data,
                expire=ttl
            )

        # Index by date for time-based queries
        date_key = event.timestamp.strftime("%Y%m%d")
        await self.storage.set(
            f"audit:date:{date_key}:{event.event_id}",
            event_data,
            expire=ttl
        )