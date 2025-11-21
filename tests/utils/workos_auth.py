"""WorkOS User Management authentication helper for tests.

Uses WorkOS User Management API (password grant flow) for authentication.
This is the standard, reliable way to get JWT tokens for testing.
"""

import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


async def authenticate_with_workos(
    email: str,
    password: str,
    workos_api_key: Optional[str] = None,
    workos_client_id: Optional[str] = None,
    workos_api_url: str = "https://api.workos.com"
) -> Optional[str]:
    """Authenticate with WorkOS User Management and get JWT access token.

    Uses the password grant flow to authenticate users.
    Returns a JWT access_token that can be used for API requests.

    Args:
        email: User email
        password: User password
        workos_api_key: WorkOS API key (defaults to WORKOS_API_KEY env var)
        workos_client_id: WorkOS Client ID (defaults to WORKOS_CLIENT_ID env var)
        workos_api_url: WorkOS API URL (defaults to https://api.workos.com)

    Returns:
        JWT access_token string if successful, None otherwise
    """
    workos_api_key = workos_api_key or os.getenv("WORKOS_API_KEY")
    workos_client_id = workos_client_id or os.getenv("WORKOS_CLIENT_ID")
    workos_api_url = workos_api_url.rstrip("/")

    if not workos_api_key or not workos_client_id:
        logger.warning("WorkOS credentials not configured (WORKOS_API_KEY, WORKOS_CLIENT_ID)")
        return None

    try:
        async with httpx.AsyncClient() as client:
            # POST /user_management/authenticate with password grant
            response = await client.post(
                f"{workos_api_url}/user_management/authenticate",
                json={
                    "client_id": workos_client_id,
                    "client_secret": workos_api_key,
                    "grant_type": "password",
                    "email": email,
                    "password": password,
                },
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                if access_token:
                    logger.info(f"✅ WorkOS authentication successful: {email}")
                    return access_token
                else:
                    logger.warning(f"No access_token in WorkOS response: {data}")
                    return None
            else:
                logger.warning(
                    f"WorkOS authentication failed ({response.status_code}): {response.text[:200]}"
                )
                return None

    except Exception as e:
        logger.warning(f"WorkOS authentication error: {e}")
        return None

