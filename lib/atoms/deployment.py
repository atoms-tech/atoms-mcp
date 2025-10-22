"""
Atoms MCP Specific Deployment Implementation

This is the Atoms-specific layer that uses the platform-agnostic base classes from pheno-sdk.
"""

from pathlib import Path

# Import from pheno-sdk/deploy-kit
try:
    # Try pheno-sdk if installed
    from pheno.kits.deploy.cloud.types import (
        DeploymentConfig,
    )
except ImportError:
    try:
        # Fall back to vendored version in atoms-mcp-prod
        from pheno_vendor.deploy_kit.cloud.types import (
            DeploymentConfig,
        )
    except ImportError as e:
        raise ImportError(
            "Could not import deployment types. "
            "Make sure pheno-sdk is installed or pheno_vendor is available."
        ) from e

# Import local Atoms deployment types
from lib import DeploymentEnvironment, DeploymentResult, HTTPHealthCheckProvider, VercelDeploymentProvider


class AtomsDeploymentConfig:
    """Atoms MCP specific deployment configuration."""

    # Atoms-specific domain mappings
    ENVIRONMENT_DOMAINS = {
        "local": "atomcp.kooshapari.com",
        "preview": "devmcp.atoms.tech",
        "production": "atomcp.kooshapari.com",
    }

    # Atoms-specific environment files
    ENVIRONMENT_FILES = {
        "preview": ".env.preview",
        "production": ".env.production",
    }

    @classmethod
    def create_config(
        cls,
        environment: DeploymentEnvironment,
        project_root: Path | None = None
    ) -> DeploymentConfig:
        """Create Atoms-specific deployment configuration.

        Args:
            environment: Deployment environment
            project_root: Project root directory (default: current directory)

        Returns:
            DeploymentConfig configured for Atoms MCP
        """
        if project_root is None:
            project_root = Path.cwd()

        # Get Atoms-specific domain
        domain = cls.ENVIRONMENT_DOMAINS.get(str(environment))

        # Get Atoms-specific env file
        env_file_name = cls.ENVIRONMENT_FILES.get(str(environment))
        env_file = project_root / env_file_name if env_file_name else None

        return DeploymentConfig(
            environment=environment,
            project_root=project_root,
            env_file=env_file,
            domain=domain,
            build_command="bash build.sh",
            install_command="pip install --upgrade pip && pip install ."
        )


class AtomsVercelDeployer:
    """Atoms MCP specific Vercel deployer.

    This wraps the platform-agnostic VercelDeploymentProvider with
    Atoms-specific configuration and behavior.
    """

    def __init__(
        self,
        environment: DeploymentEnvironment,
        project_root: Path | None = None,
        logger=None
    ):
        self.environment = environment
        self.project_root = project_root or Path.cwd()
        self.logger = logger

        # Create Atoms-specific config
        self.config = AtomsDeploymentConfig.create_config(
            environment=environment,
            project_root=self.project_root
        )

        # Create platform provider
        self.provider = VercelDeploymentProvider(
            config=self.config,
            logger=logger
        )

        # Create health checker
        self.health_checker = HTTPHealthCheckProvider(logger=logger)

    def deploy(self) -> DeploymentResult:
        """Deploy Atoms MCP to Vercel.

        Returns:
            DeploymentResult with deployment status
        """
        # Execute deployment
        result = self.provider.deploy()

        if not result.success:
            return result

        # Wait for deployment to propagate
        import time
        print("\nWaiting for deployment to propagate...")
        time.sleep(3)

        # Perform health check
        deployment_url = result.url or f"https://{self.config.domain}"
        health_url = f"{deployment_url}/health"

        print(f"\nChecking deployment health at {self.config.domain}...")

        healthy = self.health_checker.check_with_retries(
            url=health_url,
            max_retries=5,
            retry_delay=2,
            timeout=10
        )

        if healthy:
            print("✅ Health check passed!")
        else:
            print("⚠️  Warning: Could not verify deployment health")
            print("The deployment may still be propagating or there may be an issue")

        # Display Atoms-specific deployment info
        self._display_deployment_info(result)

        return result

    def _display_deployment_info(self, result: DeploymentResult):
        """Display Atoms-specific deployment information."""
        print("\n" + "-"*70)
        print("  Deployment Summary")
        print("-"*70)
        print(f"  Environment:   {self.environment}")
        print(f"  Domain:        {self.config.domain}")
        print(f"  URL:           https://{self.config.domain}")
        print(f"  MCP Endpoint:  https://{self.config.domain}/api/mcp")
        print(f"  Health Check:  https://{self.config.domain}/health")
        print("-"*70)

        print("\nDeployment completed successfully!")
        print("\nNext steps:")
        print("1. Verify the deployment at the URL above")
        print("2. Test the MCP endpoint with your client")
        print("3. Monitor logs in Vercel dashboard")

        if self.environment == DeploymentEnvironment.PRODUCTION:
            print("\n⚠️  Note: This is a PRODUCTION deployment")
            print("All users will see this version immediately")
        else:
            print("\n📝 Note: This is a PREVIEW deployment")
            print("Use for testing before promoting to production")

    def rollback(self, deployment_id: str) -> DeploymentResult:
        """Rollback Atoms MCP deployment.

        Args:
            deployment_id: ID of deployment to rollback to

        Returns:
            DeploymentResult with rollback status
        """
        return self.provider.rollback(deployment_id)

    def get_recent_deployments(self, limit: int = 10) -> list:
        """Get recent Atoms MCP deployments.

        Args:
            limit: Maximum number of deployments to return

        Returns:
            List of deployment information
        """
        return self.provider.get_deployments(limit=limit)


def deploy_atoms_to_vercel(
    environment: str,
    project_root: Path | None = None,
    logger=None
) -> int:
    """Deploy Atoms MCP to Vercel (convenience function).

    This is the function called by atoms-mcp.py CLI.

    Args:
        environment: "preview" or "production"
        project_root: Project root directory
        logger: Optional logger instance

    Returns:
        0 on success, 1 on failure
    """
    # Map string to enum
    env_map = {
        "preview": DeploymentEnvironment.PREVIEW,
        "production": DeploymentEnvironment.PRODUCTION,
    }

    env = env_map.get(environment)
    if not env:
        if logger:
            logger.error(f"Invalid environment: {environment}")
        print(f"Error: Invalid environment: {environment}")
        return 1

    # Create deployer
    deployer = AtomsVercelDeployer(
        environment=env,
        project_root=project_root,
        logger=logger
    )

    # Execute deployment
    result = deployer.deploy()

    return 0 if result.success else 1
