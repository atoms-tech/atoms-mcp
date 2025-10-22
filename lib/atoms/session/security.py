"""
Security Service

Rate limiting, session hijacking prevention, suspicious activity detection,
and comprehensive audit logging for session security.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .models import AuditAction, AuditLog, DeviceFingerprint, Session
from .storage.base import StorageBackend

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SuspiciousActivityError(Exception):
    """Raised when suspicious activity is detected."""
    pass


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    name: str
    max_requests: int
    window_seconds: int
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    max_backoff_seconds: int = 3600


@dataclass
class RateLimitState:
    """Current rate limit state for a key."""

    count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    backoff_until: datetime | None = None
    violation_count: int = 0


class SecurityService:
    """
    Provides security features for session management.

    Features:
    - Rate limiting with exponential backoff
    - Session hijacking detection
    - Suspicious activity monitoring
    - Comprehensive audit logging
    - IP address tracking
    - Device fingerprint validation
    """

    def __init__(
        self,
        storage: StorageBackend,
        enable_rate_limiting: bool = True,
        enable_hijacking_detection: bool = True,
        audit_enabled: bool = True,
    ):
        """
        Initialize security service.

        Args:
            storage: Storage backend for security data
            enable_rate_limiting: Enable rate limiting
            enable_hijacking_detection: Enable hijacking detection
            audit_enabled: Enable audit logging
        """
        self.storage = storage
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_hijacking_detection = enable_hijacking_detection
        self.audit_enabled = audit_enabled

        # Rate limiting state
        self._rate_limit_states: dict[str, dict[str, RateLimitState]] = defaultdict(dict)
        self._rate_limit_lock = asyncio.Lock()

        # Default rate limit rules
        self.rate_limit_rules: dict[str, RateLimitRule] = {
            "token_refresh": RateLimitRule(
                name="token_refresh",
                max_requests=10,
                window_seconds=60,
                exponential_backoff=True,
            ),
            "session_create": RateLimitRule(
                name="session_create",
                max_requests=5,
                window_seconds=300,
                exponential_backoff=True,
            ),
            "login_attempt": RateLimitRule(
                name="login_attempt",
                max_requests=5,
                window_seconds=300,
                exponential_backoff=True,
                max_backoff_seconds=1800,
            ),
        }

    def add_rate_limit_rule(self, rule: RateLimitRule):
        """Add or update a rate limit rule."""
        self.rate_limit_rules[rule.name] = rule
        logger.info(f"Added rate limit rule: {rule.name}")

    async def check_rate_limit(
        self,
        rule_name: str,
        key: str,
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            rule_name: Name of rate limit rule to apply
            key: Unique key for rate limiting (e.g., user_id, ip_address)

        Returns:
            True if within limit

        Raises:
            RateLimitError: If rate limit exceeded
        """
        if not self.enable_rate_limiting:
            return True

        rule = self.rate_limit_rules.get(rule_name)
        if not rule:
            logger.warning(f"Unknown rate limit rule: {rule_name}")
            return True

        async with self._rate_limit_lock:
            # Get or create state for this key
            if rule_name not in self._rate_limit_states:
                self._rate_limit_states[rule_name] = {}

            states = self._rate_limit_states[rule_name]
            if key not in states:
                states[key] = RateLimitState()

            state = states[key]
            now = datetime.utcnow()

            # Check if in backoff period
            if state.backoff_until and now < state.backoff_until:
                backoff_remaining = (state.backoff_until - now).total_seconds()

                # Audit log
                if self.audit_enabled:
                    await self._create_audit_log(
                        action=AuditAction.RATE_LIMIT_EXCEEDED,
                        details=f"Rate limit exceeded for {rule_name}: in backoff period",
                        metadata={
                            "rule_name": rule_name,
                            "key": key,
                            "backoff_remaining": backoff_remaining,
                        }
                    )

                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {backoff_remaining:.0f} seconds"
                )

            # Check if window has expired
            window_end = state.window_start + timedelta(seconds=rule.window_seconds)
            if now >= window_end:
                # Reset window
                state.count = 0
                state.window_start = now

            # Increment counter
            state.count += 1

            # Check if limit exceeded
            if state.count > rule.max_requests:
                state.violation_count += 1

                # Apply exponential backoff if enabled
                if rule.exponential_backoff:
                    backoff_seconds = min(
                        rule.window_seconds * (rule.backoff_multiplier ** (state.violation_count - 1)),
                        rule.max_backoff_seconds
                    )
                    state.backoff_until = now + timedelta(seconds=backoff_seconds)
                else:
                    state.backoff_until = now + timedelta(seconds=rule.window_seconds)

                backoff_remaining = (state.backoff_until - now).total_seconds()

                # Audit log
                if self.audit_enabled:
                    await self._create_audit_log(
                        action=AuditAction.RATE_LIMIT_EXCEEDED,
                        details=f"Rate limit exceeded for {rule_name}",
                        is_suspicious=state.violation_count > 3,
                        risk_score=min(0.2 * state.violation_count, 1.0),
                        metadata={
                            "rule_name": rule_name,
                            "key": key,
                            "count": state.count,
                            "limit": rule.max_requests,
                            "violation_count": state.violation_count,
                            "backoff_seconds": backoff_remaining,
                        }
                    )

                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {backoff_remaining:.0f} seconds"
                )

            return True

    async def detect_session_hijacking(
        self,
        session: Session,
        current_ip: str | None = None,
        current_fingerprint: DeviceFingerprint | None = None,
        current_user_agent: str | None = None,
    ) -> tuple[bool, float, list[str]]:
        """
        Detect potential session hijacking.

        Args:
            session: Session to validate
            current_ip: Current IP address
            current_fingerprint: Current device fingerprint
            current_user_agent: Current user agent

        Returns:
            Tuple of (is_suspicious, risk_score, reasons)
        """
        if not self.enable_hijacking_detection:
            return False, 0.0, []

        is_suspicious = False
        risk_score = 0.0
        reasons = []

        # Check IP address change
        if current_ip and session.ip_address and current_ip != session.ip_address:
            is_suspicious = True
            risk_score += 0.3
            reasons.append(f"IP address changed from {session.ip_address} to {current_ip}")

        # Check device fingerprint
        if (
            current_fingerprint
            and session.device_fingerprint
            and not session.device_fingerprint.matches(current_fingerprint, threshold=0.8)
        ):
            is_suspicious = True
            risk_score += 0.5
            reasons.append("Device fingerprint mismatch")

        # Check user agent change
        if (
            current_user_agent
            and session.user_agent
            and current_user_agent != session.user_agent
        ):
            is_suspicious = True
            risk_score += 0.2
            reasons.append("User agent changed")

        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)

        # Audit log if suspicious
        if is_suspicious and self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SESSION_HIJACK_ATTEMPT,
                session_id=session.session_id,
                user_id=session.user_id,
                details=f"Potential session hijacking detected: {', '.join(reasons)}",
                is_suspicious=True,
                risk_score=risk_score,
                metadata={
                    "reasons": reasons,
                    "current_ip": current_ip,
                    "session_ip": session.ip_address,
                    "current_user_agent": current_user_agent,
                    "session_user_agent": session.user_agent,
                }
            )

        return is_suspicious, risk_score, reasons

    async def detect_suspicious_activity(
        self,
        user_id: str,
        activity_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, float, list[str]]:
        """
        Detect suspicious activity patterns.

        Args:
            user_id: User identifier
            activity_type: Type of activity
            metadata: Additional metadata

        Returns:
            Tuple of (is_suspicious, risk_score, reasons)
        """
        is_suspicious = False
        risk_score = 0.0
        reasons = []

        # Get recent audit logs for user
        logs = await self.storage.get_user_audit_logs(user_id, limit=50)

        # Check for rapid session creation
        recent_creates = [
            log for log in logs
            if log.action == AuditAction.SESSION_CREATED
            and (datetime.utcnow() - log.timestamp).total_seconds() < 300
        ]
        if len(recent_creates) > 3:
            is_suspicious = True
            risk_score += 0.4
            reasons.append(f"Rapid session creation: {len(recent_creates)} in 5 minutes")

        # Check for multiple failed logins
        failed_logins = [
            log for log in logs
            if log.action == AuditAction.LOGIN_FAILURE
            and (datetime.utcnow() - log.timestamp).total_seconds() < 600
        ]
        if len(failed_logins) > 3:
            is_suspicious = True
            risk_score += 0.5
            reasons.append(f"Multiple failed logins: {len(failed_logins)} in 10 minutes")

        # Check for multiple IP addresses
        recent_ips = set(
            log.ip_address for log in logs[:10]
            if log.ip_address
        )
        if len(recent_ips) > 3:
            is_suspicious = True
            risk_score += 0.3
            reasons.append(f"Multiple IP addresses: {len(recent_ips)} IPs in recent activity")

        # Cap risk score
        risk_score = min(risk_score, 1.0)

        # Audit log if suspicious
        if is_suspicious and self.audit_enabled:
            await self._create_audit_log(
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                user_id=user_id,
                details=f"Suspicious activity detected: {', '.join(reasons)}",
                is_suspicious=True,
                risk_score=risk_score,
                metadata={
                    "activity_type": activity_type,
                    "reasons": reasons,
                    **(metadata or {}),
                }
            )

        return is_suspicious, risk_score, reasons

    async def log_security_event(
        self,
        event_type: str,
        session_id: str | None = None,
        user_id: str | None = None,
        details: str = "",
        risk_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Log a security event.

        Args:
            event_type: Type of security event
            session_id: Associated session ID
            user_id: Associated user ID
            details: Event details
            risk_score: Risk score (0.0-1.0)
            metadata: Additional metadata
        """
        if not self.audit_enabled:
            return

        # Map event type to audit action
        action_map = {
            "login_success": AuditAction.LOGIN_SUCCESS,
            "login_failure": AuditAction.LOGIN_FAILURE,
            "logout": AuditAction.LOGOUT,
            "suspicious_activity": AuditAction.SUSPICIOUS_ACTIVITY,
            "rate_limit": AuditAction.RATE_LIMIT_EXCEEDED,
        }

        action = action_map.get(event_type, AuditAction.SUSPICIOUS_ACTIVITY)

        await self._create_audit_log(
            action=action,
            session_id=session_id,
            user_id=user_id,
            details=details,
            is_suspicious=risk_score > 0.5,
            risk_score=risk_score,
            metadata=metadata or {},
        )

    async def get_security_summary(
        self,
        user_id: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        """
        Get security summary for a user.

        Args:
            user_id: User identifier
            hours: Number of hours to include

        Returns:
            Security summary with statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        logs = await self.storage.get_user_audit_logs(user_id, limit=1000)

        # Filter recent logs
        recent_logs = [log for log in logs if log.timestamp >= cutoff]

        # Calculate statistics
        total_events = len(recent_logs)
        suspicious_events = len([log for log in recent_logs if log.is_suspicious])
        failed_logins = len([
            log for log in recent_logs
            if log.action == AuditAction.LOGIN_FAILURE
        ])
        successful_logins = len([
            log for log in recent_logs
            if log.action == AuditAction.LOGIN_SUCCESS
        ])

        unique_ips = set(log.ip_address for log in recent_logs if log.ip_address)

        avg_risk_score = (
            sum(log.risk_score for log in recent_logs) / len(recent_logs)
            if recent_logs else 0.0
        )

        return {
            "user_id": user_id,
            "period_hours": hours,
            "total_events": total_events,
            "suspicious_events": suspicious_events,
            "failed_logins": failed_logins,
            "successful_logins": successful_logins,
            "unique_ips": len(unique_ips),
            "average_risk_score": avg_risk_score,
            "recent_events": [log.to_dict() for log in recent_logs[:10]],
        }

    async def _create_audit_log(
        self,
        action: AuditAction,
        session_id: str | None = None,
        user_id: str | None = None,
        details: str = "",
        is_suspicious: bool = False,
        risk_score: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ):
        """Create and store audit log entry."""
        log = AuditLog(
            action=action,
            action_details=details,
            session_id=session_id,
            user_id=user_id,
            is_suspicious=is_suspicious,
            risk_score=risk_score,
            metadata=metadata or {},
        )

        await self.storage.save_audit_log(log)
