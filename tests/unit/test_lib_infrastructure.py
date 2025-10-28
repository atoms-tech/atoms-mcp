"""Test lib.atoms.infrastructure modules for 100% coverage."""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from lib.atoms.infrastructure.deployment import AtomsDeploymentConfig, AtomsVercelDeployer, DeploymentConfig
from lib.atoms.infrastructure.infrastructure_bootstrap import AtomsInfrastructureBootstrap, InfrastructureBootstrapError

# Import infrastructure components
from lib.atoms.infrastructure.port_manager import AtomsPortManager


class TestPortManager:
    """Test port manager functionality."""

    def test_port_manager_creation(self):
        """Test port manager creation."""
        manager = AtomsPortManager(
            base_port=50000,
            max_ports=100,
            port_file="/tmp/test_ports.json"
        )

        assert manager.base_port == 50000
        assert manager.max_ports == 100
        assert manager.port_file == "/tmp/test_ports.json"

    def test_get_port_manager(self):
        """Test getting global port manager instance."""
        manager1 = AtomsPortManager.get_port_manager()
        manager2 = AtomsPortManager.get_port_manager()

        # Should return same instance
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_allocate_atoms_port(self):
        """Test port allocation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "test_ports.json")
            manager = AtomsPortManager(
                base_port=50000,
                max_ports=10,
                port_file=port_file
            )

            # Allocate first port
            port1 = await manager.allocate_atoms_port()
            assert port1 >= 50000
            assert port1 < 50010

            # Allocate second port
            port2 = await manager.allocate_atoms_port()
            assert port2 >= 50000
            assert port2 < 50010
            assert port2 != port1

            # Release first port
            await manager.release_atoms_port(port1)

            # Allocate again - should reuse first port
            port3 = await manager.allocate_atoms_port()
            assert port3 == port1

    @pytest.mark.asyncio
    async def test_port_exhaustion(self):
        """Test port exhaustion handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "test_ports.json")
            manager = AtomsPortManager(
                base_port=50000,
                max_ports=2,
                port_file=port_file
            )

            # Allocate all available ports
            await manager.allocate_atoms_port()
            await manager.allocate_atoms_port()

            # Should fail when all ports are allocated
            with pytest.raises(Exception):
                await manager.allocate_atoms_port()

    @pytest.mark.asyncio
    async def test_get_atoms_port(self):
        """Test getting allocated port."""
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "test_ports.json")
            manager = AtomsPortManager(
                base_port=50000,
                max_ports=10,
                port_file=port_file
            )

            # Allocate port
            allocated_port = await manager.allocate_atoms_port()

            # Get port - should return allocated port
            retrieved_port = await manager.get_atoms_port()
            assert retrieved_port == allocated_port

            # Release port
            await manager.release_atoms_port(allocated_port)

            # Get port - should return None (no allocated ports)
            retrieved_port = await manager.get_atoms_port()
            assert retrieved_port is None

    @pytest.mark.asyncio
    async def test_release_atoms_port(self):
        """Test port release."""
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "test_ports.json")
            manager = AtomsPortManager(
                base_port=50000,
                max_ports=10,
                port_file=port_file
            )

            # Allocate and release port
            port = await manager.allocate_atoms_port()
            await manager.release_atoms_port(port)

            # Port should be available for allocation
            new_port = await manager.allocate_atoms_port()
            assert new_port == port

    @pytest.mark.asyncio
    async def test_release_nonexistent_port(self):
        """Test releasing non-existent port."""
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "test_ports.json")
            manager = AtomsPortManager(
                base_port=50000,
                max_ports=10,
                port_file=port_file
            )

            # Should not raise error for non-existent port
            await manager.release_atoms_port(99999)

            # Should still be able to allocate ports
            port = await manager.allocate_atoms_port()
            assert port >= 50000


class TestDeployment:
    """Test deployment functionality."""

    def test_deployment_config_creation(self):
        """Test deployment configuration creation."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token",
            vercel_team_id="team-123",
            domain="test.example.com",
            build_command="npm run build",
            output_directory="dist"
        )

        assert config.project_name == "test-project"
        assert config.vercel_token == "test-token"
        assert config.vercel_team_id == "team-123"
        assert config.domain == "test.example.com"
        assert config.build_command == "npm run build"
        assert config.output_directory == "dist"

    def test_deployment_config_validation(self):
        """Test deployment configuration validation."""
        # Valid config
        valid_config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token"
        )
        assert valid_config.is_valid() is True

        # Invalid config (missing required fields)
        with pytest.raises(Exception):
            AtomsDeploymentConfig(
                project_name="",
                vercel_token=""
            )

    def test_deployment_config_serialization(self):
        """Test deployment configuration serialization."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token",
            domain="test.example.com"
        )

        # Convert to dict
        config_dict = config.to_dict()
        assert config_dict["project_name"] == "test-project"
        assert config_dict["vercel_token"] == "test-token"
        assert config_dict["domain"] == "test.example.com"
        assert "vercel_token" in config_dict

        # Mask sensitive data
        masked_dict = config.to_dict(mask_sensitive=True)
        assert masked_dict["vercel_token"] == "***MASKED***"
        assert masked_dict["project_name"] == "test-project"

    def test_vercel_deployer_creation(self):
        """Test Vercel deployer creation."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token"
        )

        deployer = AtomsVercelDeployer(config)
        assert deployer.config == config
        assert deployer.client is not None

    @pytest.mark.asyncio
    async def test_vercel_deployer_deploy_success(self):
        """Test successful Vercel deployment."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token"
        )

        deployer = AtomsVercelDeployer(config)

        # Mock successful deployment
        deployer.client = AsyncMock()
        deployer.client.deploy.return_value = {
            "deployment_url": "https://test-project.vercel.app",
            "deployment_id": "deployment-123",
            "status": "ready"
        }

        result = await deployer.deploy()

        assert result["success"] is True
        assert result["deployment_url"] == "https://test-project.vercel.app"
        assert result["deployment_id"] == "deployment-123"
        assert result["status"] == "ready"

    @pytest.mark.asyncio
    async def test_vercel_deployer_deploy_failure(self):
        """Test failed Vercel deployment."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token"
        )

        deployer = AtomsVercelDeployer(config)

        # Mock failed deployment
        deployer.client = AsyncMock()
        deployer.client.deploy.side_effect = Exception("Deployment failed")

        with pytest.raises(Exception):
            await deployer.deploy()

    @pytest.mark.asyncio
    async def test_vercel_deployer_get_deployment_status(self):
        """Test getting deployment status."""
        config = AtomsDeploymentConfig(
            project_name="test-project",
            vercel_token="test-token"
        )

        deployer = AtomsVercelDeployer(config)

        # Mock deployment status
        deployer.client = AsyncMock()
        deployer.client.get_deployment.return_value = {
            "id": "deployment-123",
            "status": "ready",
            "created_at": datetime.now().isoformat()
        }

        status = await deployer.get_deployment_status("deployment-123")

        assert status["id"] == "deployment-123"
        assert status["status"] == "ready"
        assert "created_at" in status

    def test_deployment_config_creation_comprehensive(self):
        """Test comprehensive deployment configuration."""
        config = DeploymentConfig(
            name="comprehensive-test",
            environment="production",
            variables={
                "API_URL": "https://api.example.com",
                "DATABASE_URL": "postgresql://...",
                "JWT_SECRET": "super-secret"
            },
            build_config={
                "cmd": "npm run build:prod",
                "cwd": "./frontend",
                "env": ["NODE_ENV=production"]
            },
            deploy_config={
                "type": "vercel",
                "domain": "app.example.com",
                "regions": ["iad1"]
            }
        )

        assert config.name == "comprehensive-test"
        assert config.environment == "production"
        assert config.variables["API_URL"] == "https://api.example.com"
        assert config.build_config["cmd"] == "npm run build:prod"
        assert config.deploy_config["domain"] == "app.example.com"

    def test_deployment_config_merge(self):
        """Test deployment configuration merging."""
        base_config = DeploymentConfig(
            name="base-test",
            variables={"BASE_VAR": "base_value"}
        )

        override_config = {
            "variables": {"OVERRIDE_VAR": "override_value"},
            "build_config": {"cmd": "npm run build:override"}
        }

        merged = base_config.merge(override_config)

        assert merged.variables["BASE_VAR"] == "base_value"  # Preserved
        assert merged.variables["OVERRIDE_VAR"] == "override_value"  # Added
        assert merged.build_config["cmd"] == "npm run build:override"  # Overridden


class TestInfrastructureBootstrap:
    """Test infrastructure bootstrap functionality."""

    def test_bootstrap_creation(self):
        """Test bootstrap creation."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="test-project",
            environment="development",
            config_file="/tmp/test_config.json"
        )

        assert bootstrap.project_name == "test-project"
        assert bootstrap.environment == "development"
        assert bootstrap.config_file == "/tmp/test_config.json"

    def test_bootstrap_error(self):
        """Test bootstrap error."""
        error = InfrastructureBootstrapError(
            message="Bootstrap failed",
            error_code="BOOTSTRAP_ERROR",
            details={"phase": "initialization"}
        )

        assert error.message == "Bootstrap failed"
        assert error.error_code == "BOOTSTRAP_ERROR"
        assert error.details["phase"] == "initialization"
        assert str(error) == "Bootstrap failed (BOOTSTRAP_ERROR)"

    @pytest.mark.asyncio
    async def test_bootstrap_infrastructure(self):
        """Test infrastructure bootstrap process."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "bootstrap_config.json")

            # Create test config
            test_config = {
                "project_name": "bootstrap-test",
                "environment": "development",
                "services": {
                    "database": {
                        "type": "postgresql",
                        "host": "localhost",
                        "port": 5432
                    },
                    "redis": {
                        "type": "redis",
                        "host": "localhost",
                        "port": 6379
                    }
                },
                "ports": {
                    "base": 50000,
                    "max": 10
                }
            }

            with open(config_file, "w") as f:
                import json
                json.dump(test_config, f)

            bootstrap = AtomsInfrastructureBootstrap(
                project_name="bootstrap-test",
                environment="development",
                config_file=config_file
            )

            # Mock service startup
            with patch.object(bootstrap, "_start_database_service", new=AsyncMock()) as mock_db:
                with patch.object(bootstrap, "_start_redis_service", new=AsyncMock()) as mock_redis:
                    with patch.object(bootstrap, "_allocate_ports", new=AsyncMock()) as mock_ports:

                        # Run bootstrap
                        result = await bootstrap.bootstrap_infrastructure()

                        # Should call all service startup methods
                        mock_db.assert_called_once()
                        mock_redis.assert_called_once()
                        mock_ports.assert_called_once()

                        assert result["success"] is True
                        assert result["project_name"] == "bootstrap-test"
                        assert result["environment"] == "development"

    @pytest.mark.asyncio
    async def test_bootstrap_with_custom_config(self):
        """Test bootstrap with custom configuration."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="custom-test",
            environment="production",
            custom_config={
                "custom_service": {
                    "enabled": True,
                    "config": {"key": "value"}
                }
            }
        )

        # Mock custom service
        with patch.object(bootstrap, "_start_custom_service", new=AsyncMock()) as mock_custom:
            await bootstrap.bootstrap_infrastructure()

            mock_custom.assert_called_once_with({
                "enabled": True,
                "config": {"key": "value"}
            })

    @pytest.mark.asyncio
    async def test_bootstrap_error_handling(self):
        """Test bootstrap error handling."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="error-test",
            environment="development"
        )

        # Mock service failure
        with patch.object(bootstrap, "_start_database_service", new=AsyncMock(side_effect=Exception("DB failed"))):
            with pytest.raises(InfrastructureBootstrapError) as exc_info:
                await bootstrap.bootstrap_infrastructure()

            error = exc_info.value
            assert "DB failed" in str(error)
            assert error.error_code == "SERVICE_STARTUP_ERROR"

    def test_bootstrap_port_allocation(self):
        """Test bootstrap port allocation."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="port-test",
            environment="development",
            port_config={
                "base": 50000,
                "max_ports": 5,
                "services": ["api", "websocket", "metrics"]
            }
        )

        # Mock port manager
        with patch("lib.atoms.infrastructure.port_manager.AtomsPortManager.get_port_manager") as mock_manager:
            mock_port_manager = AsyncMock()
            mock_manager.allocate_atoms_port.side_effect = [50001, 50002, 50003]
            mock_manager.return_value = mock_port_manager

            ports = asyncio.run(bootstrap._allocate_ports())

            assert ports["api"] == 50001
            assert ports["websocket"] == 50002
            assert ports["metrics"] == 50003

    @pytest.mark.asyncio
    async def test_bootstrap_service_health_checks(self):
        """Test bootstrap service health checks."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="health-test",
            environment="development"
        )

        # Mock health check
        with patch.object(bootstrap, "_check_service_health", new=AsyncMock(return_value=True)) as mock_health:
            result = await bootstrap.run_health_checks()

            assert result["all_healthy"] is True
            mock_health.assert_called()

    def test_bootstrap_config_validation(self):
        """Test bootstrap configuration validation."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="validation-test",
            environment="production"
        )

        # Valid config
        valid_config = {
            "project_name": "test-project",
            "environment": "production",
            "services": {}
        }

        assert bootstrap.validate_config(valid_config) is True

        # Invalid config (missing project name)
        invalid_config = {
            "environment": "production",
            "services": {}
        }

        assert bootstrap.validate_config(invalid_config) is False

    @pytest.mark.asyncio
    async def test_bootstrap_teardown(self):
        """Test bootstrap teardown process."""
        bootstrap = AtomsInfrastructureBootstrap(
            project_name="teardown-test",
            environment="development"
        )

        # Mock service shutdown
        with patch.object(bootstrap, "_stop_all_services", new=AsyncMock()) as mock_stop:
            result = await bootstrap.teardown_infrastructure()

            mock_stop.assert_called_once()
            assert result["success"] is True
            assert result["message"] == "Infrastructure torn down successfully"


class TestInfrastructureIntegration:
    """Test infrastructure integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_deployment_lifecycle(self):
        """Test complete deployment lifecycle."""
        # Setup deployment config
        config = AtomsDeploymentConfig(
            project_name="lifecycle-test",
            vercel_token="test-token",
            domain="lifecycle-test.example.com"
        )

        # Setup port manager
        with tempfile.TemporaryDirectory() as temp_dir:
            port_file = os.path.join(temp_dir, "ports.json")
            port_manager = AtomsPortManager(
                base_port=50000,
                max_ports=10,
                port_file=port_file
            )

            # Allocate port
            port = await port_manager.allocate_atoms_port()

            # Setup deployer
            deployer = AtomsVercelDeployer(config)

            # Mock deployment
            deployer.client = AsyncMock()
            deployer.client.deploy.return_value = {
                "deployment_url": "https://lifecycle-test.example.com",
                "deployment_id": "deployment-lifecycle-123",
                "status": "ready"
            }

            # Deploy
            deployment_result = await deployer.deploy()

            assert deployment_result["success"] is True
            assert deployment_result["deployment_url"] == "https://lifecycle-test.example.com"

            # Check deployment status
            status = await deployer.get_deployment_status("deployment-lifecycle-123")
            assert status["status"] == "ready"

            # Release port
            await port_manager.release_atoms_port(port)

    @pytest.mark.asyncio
    async def test_bootstrap_with_deployment(self):
        """Test bootstrap followed by deployment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup bootstrap
            config_file = os.path.join(temp_dir, "config.json")
            bootstrap_config = {
                "project_name": "integrated-test",
                "environment": "staging",
                "services": {
                    "api": {"type": "fastapi", "port": "auto"},
                    "database": {"type": "postgresql", "host": "localhost"}
                },
                "deployment": {
                    "type": "vercel",
                    "domain": "integrated-test.vercel.app"
                }
            }

            with open(config_file, "w") as f:
                import json
                json.dump(bootstrap_config, f)

            bootstrap = AtomsInfrastructureBootstrap(
                project_name="integrated-test",
                environment="staging",
                config_file=config_file
            )

            # Mock bootstrap and deployment
            with patch.object(bootstrap, "_start_api_service", new=AsyncMock()) as mock_api:
                with patch.object(bootstrap, "_start_database_service", new=AsyncMock()) as mock_db:
                    with patch.object(bootstrap, "_allocate_ports", new=AsyncMock(return_value={"api": 50001})) as mock_ports:

                        # Bootstrap
                        bootstrap_result = await bootstrap.bootstrap_infrastructure()

                        assert bootstrap_result["success"] is True
                        mock_api.assert_called_once()
                        mock_db.assert_called_once()
                        mock_ports.assert_called_once()

                        # Setup deployment
                        deployment_config = AtomsDeploymentConfig(
                            project_name="integrated-test",
                            vercel_token="test-token",
                            domain="integrated-test.vercel.app"
                        )

                        deployer = AtomsVercelDeployer(deployment_config)
                        deployer.client = AsyncMock()
                        deployer.client.deploy.return_value = {
                            "success": True,
                            "deployment_url": "https://integrated-test.vercel.app",
                            "deployment_id": "deployment-integrated-123"
                        }

                        # Deploy
                        deployment_result = await deployer.deploy()

                        assert deployment_result["success"] is True
                        assert deployment_result["deployment_url"] == "https://integrated-test.vercel.app"
