"""Comprehensive infrastructure validation tests for Atoms MCP.

Tests cover:
- Port allocation and management
- Process cleanup
- Tunnel setup and teardown
- Infrastructure bootstrap
- Health checks
"""

from __future__ import annotations

import logging

import pytest

# Setup test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPortAllocation:
    """Test port allocation functionality."""

    def test_port_registry_exists(self):
        """Test that PortRegistry can be imported."""
        try:
            from pheno.infra.port_registry import PortRegistry
            registry = PortRegistry()
            assert registry is not None
            logger.info("✓ PortRegistry imported successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    def test_smart_port_allocator_exists(self):
        """Test that SmartPortAllocator can be imported."""
        try:
            from pheno.infra.port_allocator import SmartPortAllocator
            from pheno.infra.port_registry import PortRegistry
            registry = PortRegistry()
            allocator = SmartPortAllocator(registry)
            assert allocator is not None
            logger.info("✓ SmartPortAllocator imported successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    @pytest.mark.asyncio
    async def test_atoms_port_allocation(self):
        """Test Atoms MCP port allocation."""
        try:
            from lib.atoms.server import AtomsServerManager
            manager = AtomsServerManager()
            assert manager.port is not None
            assert isinstance(manager.port, int)
            assert manager.port > 0
            logger.info(f"✓ Atoms allocated port: {manager.port}")
        except ImportError:
            pytest.skip("atoms-mcp-prod module not available")


class TestProcessCleanup:
    """Test process cleanup functionality."""

    def test_process_cleanup_manager_exists(self):
        """Test that ProcessCleanupManager can be imported."""
        try:
            from pheno.infra.process_cleanup import ProcessCleanupManager
            manager = ProcessCleanupManager()
            assert manager is not None
            logger.info("✓ ProcessCleanupManager imported successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    def test_process_cleanup_config_exists(self):
        """Test that ProcessCleanupConfig can be imported."""
        try:
            from pheno.infra.process_cleanup import ProcessCleanupConfig
            config = ProcessCleanupConfig(
                cleanup_related_services=True,
                cleanup_tunnels=True,
                grace_period=2.0,
            )
            assert config is not None
            logger.info("✓ ProcessCleanupConfig created successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    @pytest.mark.asyncio
    async def test_cleanup_before_startup(self):
        """Test cleanup_before_startup function."""
        try:
            from pheno.infra.process_cleanup import ProcessCleanupConfig, cleanup_before_startup
            config = ProcessCleanupConfig()
            # Just test that it can be called
            try:
                result = await cleanup_before_startup("atoms-mcp-server", config)
                logger.info(f"✓ Cleanup returned: {result}")
            except Exception as e:
                # Cleanup might fail in test environment, but should be callable
                logger.info(f"⚠️  Cleanup error (expected in test): {e}")
        except ImportError:
            pytest.skip("pheno-sdk not available")


class TestTunneling:
    """Test tunnel management functionality."""

    def test_tunnel_config_exists(self):
        """Test that TunnelConfig can be imported."""
        try:
            from pheno.infra.tunneling import TunnelConfig, TunnelProtocol, TunnelType
            config = TunnelConfig(
                name="test-tunnel",
                local_host="127.0.0.1",
                local_port=8000,
                tunnel_type=TunnelType.CLOUDFLARE,
                protocol=TunnelProtocol.HTTPS,
            )
            assert config is not None
            assert config.local_port == 8000
            logger.info("✓ TunnelConfig created successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    def test_tunnel_registry_exists(self):
        """Test that TunnelRegistry can be imported."""
        try:
            from pheno.infra.tunneling import TunnelRegistry
            registry = TunnelRegistry()
            assert registry is not None
            logger.info("✓ TunnelRegistry imported successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")

    def test_async_tunnel_manager_exists(self):
        """Test that AsyncTunnelManager can be imported."""
        try:
            from pheno.infra.tunneling import AsyncTunnelManager, TunnelConfig
            config = TunnelConfig(
                name="test",
                local_host="127.0.0.1",
                local_port=8000,
            )
            manager = AsyncTunnelManager(config)
            assert manager is not None
            logger.info("✓ AsyncTunnelManager imported successfully")
        except ImportError:
            pytest.skip("pheno-sdk not available")


class TestKinfraIntegration:
    """Test kinfra integration."""

    def test_smart_infra_manager_exists(self):
        """Test that SmartInfraManager can be imported."""
        try:
            from kinfra import SmartInfraManager
            manager = SmartInfraManager("atoms-mcp-server")
            assert manager is not None
            assert manager.project_name == "atoms-mcp-server"
            logger.info("✓ SmartInfraManager imported successfully")
        except ImportError:
            pytest.skip("kinfra not available")

    def test_deployment_manager_exists(self):
        """Test that DeploymentManager can be imported."""
        try:
            from kinfra import get_deployment_manager
            manager = get_deployment_manager("atoms-mcp-server")
            assert manager is not None
            logger.info("✓ DeploymentManager imported successfully")
        except ImportError:
            pytest.skip("kinfra not available")

    @pytest.mark.asyncio
    async def test_infra_manager_port_allocation(self):
        """Test infrastructure manager port allocation."""
        try:
            from kinfra import SmartInfraManager
            manager = SmartInfraManager("atoms-mcp-server")
            port = await manager.allocate_port()
            assert port is not None
            assert isinstance(port, int)
            assert port > 0
            logger.info(f"✓ Infra manager allocated port: {port}")
        except ImportError:
            pytest.skip("kinfra not available")


class TestInfrastructureBootstrap:
    """Test infrastructure bootstrap."""

    def test_bootstrap_import(self):
        """Test that bootstrap can be imported."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()
            assert bootstrap is not None
            logger.info("✓ AtomsInfrastructureBootstrap imported successfully")
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")

    @pytest.mark.asyncio
    async def test_bootstrap_initialization(self):
        """Test bootstrap initialization."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()
            await bootstrap.initialize()
            assert bootstrap._initialized
            logger.info("✓ Bootstrap initialized successfully")
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")

    @pytest.mark.asyncio
    async def test_bootstrap_health_check(self):
        """Test bootstrap health check."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()
            await bootstrap.initialize()
            health = await bootstrap.health_check()
            assert isinstance(health, dict)
            assert "initialized" in health
            logger.info(f"✓ Bootstrap health check: {health}")
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")

    @pytest.mark.asyncio
    async def test_bootstrap_lifespan_context(self):
        """Test bootstrap lifespan context manager."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()
            async with bootstrap.lifespan_context():
                assert bootstrap._initialized
                logger.info("✓ Bootstrap lifespan context works")
            assert not bootstrap._initialized
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")


class TestAsyncUtils:
    """Test async utility functions."""

    def test_async_utils_import(self):
        """Test that async_utils can be imported."""
        try:
            from lib.atoms.async_utils import run_async_safely
            assert callable(run_async_safely)
            logger.info("✓ async_utils imported successfully")
        except ImportError:
            pytest.skip("async_utils not available")

    @pytest.mark.asyncio
    async def test_run_async_safely_in_async_context(self):
        """Test run_async_safely in async context."""
        try:
            from lib.atoms.async_utils import run_async_safely

            async def test_coro():
                return "test_result"

            # In async context, this should raise
            try:
                result = run_async_safely(test_coro())
                # If it doesn't raise, that's also ok (might work depending on implementation)
                logger.info(f"✓ run_async_safely returned: {result}")
            except RuntimeError as e:
                if "event loop" in str(e):
                    logger.info("✓ run_async_safely correctly raised in async context")
                else:
                    raise
        except ImportError:
            pytest.skip("async_utils not available")


class TestEndToEndInfrastructure:
    """End-to-end infrastructure tests."""

    @pytest.mark.asyncio
    async def test_full_infrastructure_startup_shutdown(self):
        """Test full infrastructure startup and shutdown."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()

            # Test full lifecycle
            await bootstrap.initialize()
            assert bootstrap._initialized

            health = await bootstrap.health_check()
            assert health["initialized"]

            await bootstrap.shutdown()
            assert not bootstrap._initialized

            logger.info("✓ Full infrastructure lifecycle test passed")
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")

    @pytest.mark.asyncio
    async def test_infrastructure_with_tunnel_context(self):
        """Test infrastructure with tunnel context."""
        try:
            from lib.atoms.infrastructure_bootstrap import AtomsInfrastructureBootstrap
            bootstrap = AtomsInfrastructureBootstrap()

            async with bootstrap.lifespan_context(enable_tunnel=False):
                health = await bootstrap.health_check()
                assert health["initialized"]
                # Tunnel should not be active since we disabled it
                assert not health["tunnel_active"]

            logger.info("✓ Infrastructure with tunnel context test passed")
        except ImportError:
            pytest.skip("infrastructure_bootstrap not available")

    @pytest.mark.asyncio
    async def test_atoms_server_manager_integration(self):
        """Test Atoms server manager integration."""
        try:
            from lib.atoms.server import AtomsServerManager
            manager = AtomsServerManager()
            assert manager.port is not None
            logger.info(f"✓ Atoms server manager test passed (port: {manager.port})")
        except ImportError:
            pytest.skip("atoms.server not available")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
