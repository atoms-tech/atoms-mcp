"""
Atoms MCP Production - Unified Startup Framework

BEFORE: 200+ lines of manual setup
AFTER: <20 lines with unified startup

This is the new, simplified startup using pheno-sdk's unified framework.
"""
import asyncio
import sys
from pathlib import Path

# Add pheno-sdk to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pheno-sdk" / "src"))

from pheno.application.services.startup_config_builder import StartupConfig
from pheno.application.services.startup_service import StartupService


async def main():
    """
    Main startup function.

    BEFORE (200+ lines):
    - Manual service manager setup
    - Manual port allocation
    - Manual PostgreSQL startup
    - Manual NATS startup
    - Manual Redis startup
    - Manual error handling
    - Manual cleanup

    AFTER (<20 lines):
    - Declarative configuration
    - Automatic resource management
    - Automatic error handling
    - Automatic cleanup
    """
    # Build configuration (fluent API)
    config = (
        StartupConfig.for_project("atoms-mcp")
        .with_postgres(database="atoms")
        .with_nats()
        .with_redis()
        .with_ports(api=8000, admin=8001)
        .with_env(
            LOG_LEVEL="INFO",
            ENVIRONMENT="production"
        )
        .build()
    )

    # Execute startup
    service = StartupService()
    result = await service.startup(config)

    # Check result
    if result.is_successful():
        print("✅ Atoms MCP Production startup complete!")
        print(result.get_summary())

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            await service.shutdown()
            print("✅ Shutdown complete")
    else:
        print("❌ Startup failed!")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

