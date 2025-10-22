"""
Complete Session Management Example

Demonstrates all features including token refresh, revocation,
security, and storage backends.
"""

import asyncio
import logging

from atoms.session import (
    DeviceFingerprint,
    RevocationService,
    SecurityService,
    SessionManager,
    TokenManager,
)
from atoms.session.storage import InMemoryStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run complete session management example."""

    # Initialize storage backend
    storage = InMemoryStorage()

    # Initialize token manager
    token_manager = TokenManager(
        storage=storage,
        token_endpoint="https://openrouter.ai/api/v1/auth/token",
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    # Initialize session manager
    session_manager = SessionManager(
        storage=storage,
        token_manager=token_manager,
        default_idle_timeout_minutes=30,
        default_absolute_timeout_minutes=480,
        max_sessions_per_user=5,
        device_validation_enabled=True,
    )

    # Initialize revocation service
    revocation_service = RevocationService(
        storage=storage,
        enable_cascading=True,
    )

    # Initialize security service
    security_service = SecurityService(
        storage=storage,
        enable_rate_limiting=True,
        enable_hijacking_detection=True,
    )

    try:
        # 1. Create session with device fingerprint
        logger.info("Creating session...")

        device_fingerprint = DeviceFingerprint(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            platform="MacIntel",
            timezone="America/New_York",
            screen_resolution="1920x1080",
            color_depth=24,
            touch_support=False,
        )

        session = await session_manager.create_session(
            user_id="user_123",
            access_token="initial_access_token",
            refresh_token="initial_refresh_token",
            expires_in=3600,
            scopes=["openid", "profile", "email"],
            device_fingerprint=device_fingerprint,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            metadata={"login_method": "oauth"},
        )

        logger.info(f"Created session: {session.session_id}")
        logger.info(f"Session state: {session.state}")
        logger.info(f"Expires at: {session.access_token_expires_at}")

        # 2. Check rate limiting
        logger.info("\nChecking rate limits...")

        try:
            await security_service.check_rate_limit(
                rule_name="token_refresh",
                key=session.user_id,
            )
            logger.info("Rate limit check passed")
        except Exception as e:
            logger.error(f"Rate limit exceeded: {e}")

        # 3. Detect session hijacking
        logger.info("\nChecking for session hijacking...")

        is_suspicious, risk_score, reasons = await security_service.detect_session_hijacking(
            session=session,
            current_ip=session.ip_address,
            current_fingerprint=device_fingerprint,
            current_user_agent=session.user_agent,
        )

        logger.info(f"Suspicious: {is_suspicious}, Risk: {risk_score}")
        if reasons:
            logger.info(f"Reasons: {', '.join(reasons)}")

        # 4. Retrieve session
        logger.info("\nRetrieving session...")

        retrieved_session = await session_manager.get_session(
            session.session_id,
            device_fingerprint=device_fingerprint,
            ip_address=session.ip_address,
        )

        logger.info(f"Retrieved session: {retrieved_session.session_id}")
        logger.info(f"Last accessed: {retrieved_session.last_accessed_at}")

        # 5. Check if refresh needed
        logger.info("\nChecking token refresh...")

        needs_refresh = session.needs_refresh(buffer_minutes=5)
        logger.info(f"Needs refresh: {needs_refresh}")

        # 6. Refresh token (if needed)
        if needs_refresh:
            logger.info("Refreshing token...")

            try:
                updated_session, refresh_record = await token_manager.refresh_token(
                    session=session,
                    reason="proactive",
                )

                logger.info("Token refreshed successfully")
                logger.info(f"Refresh record ID: {refresh_record.record_id}")
                logger.info(f"Rotation enabled: {refresh_record.rotation_enabled}")

                session = updated_session

            except Exception as e:
                logger.error(f"Token refresh failed: {e}")

        # 7. Get refresh history
        logger.info("\nGetting refresh history...")

        refresh_history = await token_manager.get_refresh_history(
            session_id=session.session_id,
            limit=10,
        )

        logger.info(f"Found {len(refresh_history)} refresh records")
        for record in refresh_history:
            logger.info(
                f"  - {record.refreshed_at}: {record.refresh_reason} "
                f"(rotation: {record.rotation_enabled})"
            )

        # 8. Get user sessions
        logger.info("\nGetting user sessions...")

        user_sessions = await session_manager.get_user_sessions(session.user_id)
        logger.info(f"User has {len(user_sessions)} sessions")

        for s in user_sessions:
            logger.info(f"  - {s.session_id}: {s.state} (created: {s.created_at})")

        # 9. Update session metadata
        logger.info("\nUpdating session metadata...")

        updated_session = await session_manager.update_session(
            session_id=session.session_id,
            metadata={
                "last_action": "example_action",
                "action_count": 42,
            }
        )

        logger.info(f"Updated metadata: {updated_session.metadata}")

        # 10. Security summary
        logger.info("\nGetting security summary...")

        security_summary = await security_service.get_security_summary(
            user_id=session.user_id,
            hours=24,
        )

        logger.info(f"Total events: {security_summary['total_events']}")
        logger.info(f"Suspicious events: {security_summary['suspicious_events']}")
        logger.info(f"Average risk score: {security_summary['average_risk_score']:.2f}")

        # 11. Revoke token
        logger.info("\nRevoking access token...")

        revocation_record = await revocation_service.revoke_token(
            token=session.access_token,
            token_type="access_token",
            session_id=session.session_id,
            user_id=session.user_id,
            reason="example_revocation",
        )

        logger.info(f"Token revoked: {revocation_record.revocation_id}")

        # 12. Check if token is revoked
        is_revoked = await revocation_service.is_revoked(
            token=session.access_token,
            check_storage=True,
        )

        logger.info(f"Token is revoked: {is_revoked}")

        # 13. Revoke entire session
        logger.info("\nRevoking entire session...")

        revocation_records = await revocation_service.revoke_session(
            session=session,
            reason="example_session_revocation",
        )

        logger.info(f"Revoked {len(revocation_records)} tokens")

        # 14. Verify session state
        revoked_session = await session_manager.storage.get_session(session.session_id)
        logger.info(f"Session state after revocation: {revoked_session.state}")

        # 15. Cleanup
        logger.info("\nCleaning up...")

        expired_count = await session_manager.cleanup_expired_sessions()
        logger.info(f"Cleaned up {expired_count} expired sessions")

        revocation_count = await revocation_service.cleanup_expired_revocations()
        logger.info(f"Cleaned up {revocation_count} expired revocations")

        logger.info("\n✅ Example completed successfully!")

    except Exception as e:
        logger.error(f"Error during example: {e}", exc_info=True)

    finally:
        # Cleanup
        await token_manager.close()
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
