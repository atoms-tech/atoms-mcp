"""Security Infrastructure

Provides rate limiting, input validation, and sanitization for all operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import re
from html import escape
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# RATE LIMITING (Distributed via Upstash Redis)
# ============================================================================

class UserRateLimiter:
    """Per-user rate limiting to prevent abuse.
    
    NOTE: Use get_rate_limiter() function instead of instantiating directly.
    This class is kept for backwards compatibility only.
    For production, use get_distributed_rate_limiter() from distributed_rate_limiter.py
    """

    def __init__(self):
        self.user_requests: Dict[str, List[tuple]] = {}
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 req/min
            "search": {"requests": 30, "window": 60},     # 30 searches/min
            "create": {"requests": 50, "window": 60},     # 50 creates/min
            "update": {"requests": 50, "window": 60},     # 50 updates/min
            "delete": {"requests": 20, "window": 60},     # 20 deletes/min
        }

    async def check_rate_limit(
        self,
        user_id: str,
        operation_type: str = "default"
    ) -> Dict[str, Any]:
        """Check if user has exceeded rate limit (in-memory fallback).

        Args:
            user_id: User ID to check
            operation_type: Type of operation (default, search, create, etc.)

        Returns:
            Dict with allowed (bool), limit info, and retry_after if blocked
        """
        now = datetime.now(timezone.utc)
        limit_config = self.limits.get(operation_type, self.limits["default"])
        window_seconds = limit_config["window"]
        max_requests = limit_config["requests"]

        # Initialize user tracking
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        # Clean old requests outside window
        cutoff = now - timedelta(seconds=window_seconds)
        self.user_requests[user_id] = [
            (ts, op) for ts, op in self.user_requests[user_id]
            if ts > cutoff
        ]

        # Count requests in current window
        current_count = len(self.user_requests[user_id])

        if current_count >= max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}: {current_count}/{max_requests}")
            return {
                "allowed": False,
                "limit": max_requests,
                "window_seconds": window_seconds,
                "current_count": current_count,
                "retry_after": window_seconds,
                "error": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s"
            }

        # Add current request
        self.user_requests[user_id].append((now, operation_type))

        return {
            "allowed": True,
            "limit": max_requests,
            "window_seconds": window_seconds,
            "current_count": current_count + 1,
            "remaining": max_requests - current_count - 1
        }

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit stats for user (in-memory only)"""
        if user_id not in self.user_requests:
            return {"active_requests": 0}

        # Clean old requests
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=60)
        active_requests = [
            (ts, op) for ts, op in self.user_requests[user_id]
            if ts > cutoff
        ]

        return {
            "active_requests": len(active_requests),
            "requests_by_type": {}
        }


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Validate and sanitize user inputs"""

    @staticmethod
    def validate_entity_id(entity_id: str) -> bool:
        """Validate entity ID format (UUID or WorkOS ID)"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        workos_pattern = r'^user_[A-Z0-9]{26}$'

        return (
            bool(re.match(uuid_pattern, entity_id, re.IGNORECASE)) or
            bool(re.match(workos_pattern, entity_id))
        )

    @staticmethod
    def sanitize_search_term(search_term: str) -> str:
        """Sanitize search input to prevent injection"""
        # Remove SQL injection attempts
        dangerous_patterns = [
            r"('\s*OR\s*')",
            r"('\s*AND\s*')",
            r"(--)",
            r"(;)",
            r"(/\*)",
            r"(\*/)",
            r"(xp_)",
            r"(exec\s)",
            r"(execute\s)",
            r"(drop\s)",
            r"(delete\s)",
            r"(truncate\s)"
        ]

        sanitized = search_term
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        # Escape HTML
        sanitized = escape(sanitized)

        # Limit length
        return sanitized[:500]

    @staticmethod
    def validate_data_object(data: Dict[str, Any], entity_type: str) -> Dict[str, List[str]]:
        """Validate data object for entity creation/update"""
        errors = {}

        # Required fields by entity type
        required_fields = {
            "organization": ["name"],
            "project": ["name", "organization_id"],
            "document": ["name", "project_id"],
            "requirement": ["name", "document_id"],
            "test": ["name"],
            "risk": ["name", "description"]
        }

        if entity_type in required_fields:
            for field in required_fields[entity_type]:
                if field not in data or not data[field]:
                    errors.setdefault(field, []).append(f"{field} is required")

        # Field type validation
        if "name" in data and not isinstance(data["name"], str):
            errors.setdefault("name", []).append("name must be a string")
        elif "name" in data and len(data["name"]) > 255:
            errors.setdefault("name", []).append("name too long (max 255 characters)")

        if "description" in data and isinstance(data["description"], str) and len(data["description"]) > 5000:
            errors.setdefault("description", []).append("description too long (max 5000 characters)")

        return errors

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize a string value"""
        if not isinstance(value, str):
            return str(value)[:max_length]

        # Remove null bytes
        value = value.replace('\x00', '')

        # Escape HTML
        value = escape(value)

        # Limit length
        return value[:max_length]


# Global instances
_rate_limiter: Optional[UserRateLimiter] = None
_input_validator: Optional[InputValidator] = None


def get_rate_limiter() -> UserRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = UserRateLimiter()
        logger.info("Rate limiter initialized")
    return _rate_limiter


def get_input_validator() -> InputValidator:
    """Get global input validator instance"""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
        logger.info("Input validator initialized")
    return _input_validator
