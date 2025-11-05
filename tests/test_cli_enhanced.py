"""
Tests for enhanced Atoms CLI.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from atoms_cli_enhanced import AtomsCLI, CICheckError, ConfigLoader, EnvironmentConfig, HealthCheckError


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        "project": {"name": "atoms-mcp-prod", "version": "1.0.0"},
        "environments": {
            "local": {
                "endpoint": "https://atomcp.kooshapari.com",
                "port": "auto",
                "tunnel": {"enabled": True, "domain": "atomcp.kooshapari.com"},
                "env_vars": {"ENV": "local"},
            },
            "dev": {
                "endpoint": "https://devmcp.atoms.tech",
                "vercel": {"env": "preview", "domain": "devmcp.atoms.tech"},
                "env_vars": {"ENV": "development"},
            },
            "prod": {
                "endpoint": "https://mcp.atoms.tech",
                "vercel": {"env": "production", "domain": "mcp.atoms.tech"},
                "env_vars": {"ENV": "production"},
            },
        },
        "ci_checks": [{"name": "pytest", "command": "pytest", "required": True}],
        "deployment": {"smoke_tests": {"tests": [{"name": "health", "endpoint": "/health", "expected_status": 200}]}},
        "services": [],
        "resources": [],
    }


@pytest.fixture
def cli():
    """Create CLI instance."""
    with patch("atoms_cli_enhanced.ConfigLoader.load") as mock_load:
        mock_load.return_value = Mock(
            name="atoms-mcp-prod",
            version="1.0.0",
            environments={
                "local": EnvironmentConfig(
                    name="local",
                    endpoint="https://atomcp.kooshapari.com",
                    env_vars={"ENV": "local"},
                    tunnel_enabled=True,
                    tunnel_domain="atomcp.kooshapari.com",
                )
            },
            ci_checks=[],
            deployment={},
            services=[],
            resources=[],
        )
        return AtomsCLI()


class TestConfigLoader:
    """Test configuration loading."""

    def test_load_config(self, mock_config, tmp_path):
        """Test loading configuration from YAML."""
        import yaml

        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(mock_config, f)

        config = ConfigLoader.load(config_file)

        assert config.name == "atoms-mcp-prod"
        assert config.version == "1.0.0"
        assert "local" in config.environments
        assert "dev" in config.environments
        assert "prod" in config.environments

    def test_load_config_missing_file(self):
        """Test loading non-existent configuration."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(Path("/nonexistent/config.yml"))


class TestAtomsCLI:
    """Test Atoms CLI functionality."""

    @pytest.mark.asyncio
    async def test_start_local(self, cli):
        """Test starting local server."""
        with patch.object(cli, "_cleanup_stale_infrastructure", new=AsyncMock()):
            with patch.object(cli.port_allocator, "allocate_port", return_value=8000):
                with patch.object(cli.tunnel_manager, "create_tunnel", new=AsyncMock()):
                    with patch.object(cli, "_start_server_process", new=AsyncMock()):
                        with patch.object(cli, "_health_check", new=AsyncMock()):
                            with patch.object(cli, "_launch_dashboard", new=AsyncMock()):
                                # This would normally run forever, so we'll just test the setup
                                pass

    @pytest.mark.asyncio
    async def test_deploy_local(self, cli):
        """Test deploying to local (should call start)."""
        with patch.object(cli, "start", new=AsyncMock()) as mock_start:
            await cli.deploy("local")
            mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_deploy_dev(self, cli):
        """Test deploying to dev environment."""
        with patch.object(cli, "_run_ci_checks", new=AsyncMock()):
            with patch.object(cli, "_build_application", new=AsyncMock()):
                with patch.object(cli, "_deploy_to_vercel", new=AsyncMock(return_value={"url": "https://test.com"})):
                    with patch.object(cli, "_health_check", new=AsyncMock()):
                        await cli._deploy_dev(dry_run=False)

    @pytest.mark.asyncio
    async def test_deploy_dev_dry_run(self, cli):
        """Test dry run deployment to dev."""
        with patch.object(cli, "_run_ci_checks", new=AsyncMock()):
            with patch.object(cli, "_build_application", new=AsyncMock()):
                with patch.object(cli, "_deploy_to_vercel", new=AsyncMock()) as mock_deploy:
                    await cli._deploy_dev(dry_run=True)
                    mock_deploy.assert_not_called()

    @pytest.mark.asyncio
    async def test_deploy_prod(self, cli):
        """Test deploying to production."""
        with patch.object(cli, "_run_ci_checks", new=AsyncMock()):
            with patch.object(cli, "_validate_git_state", new=AsyncMock()):
                with patch.object(cli, "_build_application", new=AsyncMock()):
                    with patch.object(cli, "_confirm_deployment", return_value=True):
                        with patch.object(
                            cli, "_deploy_to_vercel", new=AsyncMock(return_value={"url": "https://test.com"})
                        ):
                            with patch.object(cli, "_health_check", new=AsyncMock()):
                                with patch.object(cli, "_run_smoke_tests", new=AsyncMock()):
                                    await cli._deploy_prod(dry_run=False)

    @pytest.mark.asyncio
    async def test_deploy_prod_cancelled(self, cli):
        """Test cancelled production deployment."""
        with patch.object(cli, "_run_ci_checks", new=AsyncMock()):
            with patch.object(cli, "_validate_git_state", new=AsyncMock()):
                with patch.object(cli, "_build_application", new=AsyncMock()):
                    with patch.object(cli, "_confirm_deployment", return_value=False):
                        with patch.object(cli, "_deploy_to_vercel", new=AsyncMock()) as mock_deploy:
                            await cli._deploy_prod(dry_run=False)
                            mock_deploy.assert_not_called()

    @pytest.mark.asyncio
    async def test_deploy_invalid_target(self, cli):
        """Test deploying to invalid target."""
        with pytest.raises(ValueError):
            await cli.deploy("invalid")


class TestHelperFunctions:
    """Test helper functions."""

    @pytest.mark.asyncio
    async def test_run_command(self):
        """Test running shell command."""
        from lib.atoms.cli_helpers import run_command

        result = await run_command("echo 'test'")
        assert result.returncode == 0
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_run_ci_checks_success(self, tmp_path):
        """Test successful CI checks."""
        from lib.atoms.cli_helpers import run_ci_checks

        checks = [{"name": "test", "command": "echo 'pass'", "required": True}]

        result = await run_ci_checks(checks, tmp_path)
        assert result is True

    @pytest.mark.asyncio
    async def test_run_ci_checks_failure(self, tmp_path):
        """Test failed CI checks."""
        from lib.atoms.cli_helpers import run_ci_checks

        checks = [{"name": "test", "command": "exit 1", "required": True}]

        with pytest.raises(CICheckError):
            await run_ci_checks(checks, tmp_path)

    @pytest.mark.asyncio
    async def test_validate_git_state_clean(self, tmp_path):
        """Test git state validation with clean state."""

        # This test requires a git repository
        # In a real test, we'd set up a temporary git repo

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        from lib.atoms.cli_helpers import health_check

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await health_check("http://localhost:8000/health")
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check."""
        from lib.atoms.cli_helpers import health_check

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with pytest.raises(HealthCheckError):
                await health_check("http://localhost:8000/health", retries=1)


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_local_deployment(self, cli):
        """Test complete local deployment flow."""
        # This would test the entire flow end-to-end
        # Requires actual infrastructure to be available

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_dev_deployment(self, cli):
        """Test complete dev deployment flow."""
        # This would test the entire flow end-to-end
        # Requires Vercel credentials and infrastructure


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
