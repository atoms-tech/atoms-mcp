"""User ID Mapping System

Maps WorkOS user IDs (user_XXX format) to Supabase UUIDs for database compatibility.
Provides automatic conversion and caching for performance.
"""

import re
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class UserIDMapper:
    """Maps WorkOS user IDs to Supabase UUIDs and vice versa."""

    def __init__(self, database_adapter=None):
        """Initialize the mapper with database adapter.

        Args:
            database_adapter: Database adapter for querying mappings
        """
        self._db = database_adapter
        self._cache: Dict[str, str] = {}  # workos_id -> uuid
        self._reverse_cache: Dict[str, str] = {}  # uuid -> workos_id

    @staticmethod
    def is_workos_id(user_id: str) -> bool:
        """Check if ID is in WorkOS format.

        Args:
            user_id: ID to check

        Returns:
            True if WorkOS format (user_XXXX...)
        """
        return bool(re.match(r'^user_[A-Z0-9]{26}$', user_id))

    @staticmethod
    def is_uuid(user_id: str) -> bool:
        """Check if ID is in UUID format.

        Args:
            user_id: ID to check

        Returns:
            True if UUID format
        """
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, user_id, re.IGNORECASE))

    async def workos_to_uuid(self, workos_id: str) -> str:
        """Convert WorkOS user ID to UUID.

        Args:
            workos_id: WorkOS user ID (user_XXX format)

        Returns:
            Corresponding UUID

        Raises:
            ValueError: If ID format is invalid
        """
        if not self.is_workos_id(workos_id):
            raise ValueError(f"Invalid WorkOS ID format: {workos_id}")

        # Check cache first
        if workos_id in self._cache:
            logger.debug(f"Cache hit for WorkOS ID: {workos_id}")
            return self._cache[workos_id]

        # Query database
        try:
            result = await self._db.get_single(
                "user_id_mappings",
                filters={"workos_user_id": workos_id},
                select="supabase_uuid"
            )

            if result:
                uuid = result["supabase_uuid"]
                # Update cache
                self._cache[workos_id] = uuid
                self._reverse_cache[uuid] = workos_id
                logger.debug(f"Found mapping: {workos_id} -> {uuid}")
                return uuid

            # No mapping exists - this shouldn't happen if ensure_mapping was called
            logger.warning(f"No mapping found for WorkOS ID: {workos_id}")
            return await self.ensure_mapping(workos_id)

        except Exception as e:
            logger.error(f"Error converting WorkOS ID to UUID: {e}")
            raise

    async def uuid_to_workos(self, uuid: str) -> Optional[str]:
        """Convert UUID to WorkOS user ID.

        Args:
            uuid: Supabase UUID

        Returns:
            Corresponding WorkOS user ID, or None if not found

        Raises:
            ValueError: If UUID format is invalid
        """
        if not self.is_uuid(uuid):
            raise ValueError(f"Invalid UUID format: {uuid}")

        # Check cache first
        if uuid in self._reverse_cache:
            logger.debug(f"Cache hit for UUID: {uuid}")
            return self._reverse_cache[uuid]

        # Query database
        try:
            result = await self._db.get_single(
                "user_id_mappings",
                filters={"supabase_uuid": uuid},
                select="workos_user_id"
            )

            if result:
                workos_id = result["workos_user_id"]
                # Update cache
                self._cache[workos_id] = uuid
                self._reverse_cache[uuid] = workos_id
                logger.debug(f"Found mapping: {uuid} -> {workos_id}")
                return workos_id

            logger.debug(f"No mapping found for UUID: {uuid}")
            return None

        except Exception as e:
            logger.error(f"Error converting UUID to WorkOS ID: {e}")
            raise

    async def ensure_mapping(self, workos_id: str) -> str:
        """Ensure a UUID mapping exists for WorkOS ID, creating if needed.

        Args:
            workos_id: WorkOS user ID

        Returns:
            UUID (existing or newly created)

        Raises:
            ValueError: If ID format is invalid
        """
        if not self.is_workos_id(workos_id):
            raise ValueError(f"Invalid WorkOS ID format: {workos_id}")

        # Check if mapping already exists
        try:
            existing_uuid = await self.workos_to_uuid(workos_id)
            return existing_uuid
        except Exception:
            pass

        # Create new mapping
        try:
            logger.info(f"Creating new UUID mapping for WorkOS ID: {workos_id}")

            # Use database function for atomic create
            from supabase_client import get_supabase
            supabase = get_supabase()

            result = supabase.rpc(
                'get_or_create_uuid_for_workos',
                {'p_workos_id': workos_id}
            ).execute()

            if result.data:
                uuid = result.data
                # Update cache
                self._cache[workos_id] = uuid
                self._reverse_cache[uuid] = workos_id
                logger.info(f"Created mapping: {workos_id} -> {uuid}")
                return uuid
            else:
                raise Exception("Failed to create UUID mapping")

        except Exception as e:
            logger.error(f"Error ensuring mapping for {workos_id}: {e}")
            raise

    async def convert_if_needed(self, user_id: str) -> str:
        """Convert user ID to UUID if it's in WorkOS format.

        Args:
            user_id: User ID (WorkOS or UUID format)

        Returns:
            UUID (converted or original)
        """
        if self.is_workos_id(user_id):
            return await self.ensure_mapping(user_id)
        elif self.is_uuid(user_id):
            return user_id
        else:
            raise ValueError(f"Invalid user ID format: {user_id}")

    def clear_cache(self):
        """Clear the internal cache. Useful for testing."""
        self._cache.clear()
        self._reverse_cache.clear()
        logger.debug("User ID mapper cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dict with cache sizes
        """
        return {
            "workos_to_uuid_entries": len(self._cache),
            "uuid_to_workos_entries": len(self._reverse_cache)
        }


# Global instance (initialized with database adapter when needed)
_user_mapper: Optional[UserIDMapper] = None


def get_user_mapper(database_adapter=None) -> UserIDMapper:
    """Get or create global UserIDMapper instance.

    Args:
        database_adapter: Database adapter (required on first call)

    Returns:
        UserIDMapper instance
    """
    global _user_mapper

    if _user_mapper is None:
        if database_adapter is None:
            raise ValueError("Database adapter required for first initialization")
        _user_mapper = UserIDMapper(database_adapter)
        logger.info("User ID mapper initialized")

    return _user_mapper
