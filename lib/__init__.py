"""
Atoms MCP Library

Modular, framework-agnostic deployment and server management.

Architecture:
- pheno-sdk/deploy-kit/base/         → Abstract interfaces (migrated to pheno-sdk)
- pheno-sdk/deploy-kit/platforms/    → Platform implementations (migrated to pheno-sdk)
- lib/atoms/                         → Atoms-specific implementations (stays in atoms_mcp-old)

Base and platform layers have been migrated to pheno-sdk/deploy-kit.
Atoms-specific logic remains in the atoms_mcp-old repository.
"""

# Core types (from pheno-sdk/deploy-kit cloud/types)
try:
    # Try pheno-sdk if installed
    from pheno.kits.deploy.cloud.types import (
        DeploymentConfig,
        DeploymentStatus,
        DeploymentState,
    )
except ImportError:
    try:
        # Fall back to vendored version in atoms-mcp-prod
        from pheno_vendor.deploy_kit.cloud.types import (
            DeploymentConfig,
            DeploymentStatus,
            DeploymentState,
        )
    except ImportError as e:
        raise ImportError(
            "Could not import deployment types from pheno-sdk or vendored deploy_kit. "
            "Make sure pheno-sdk is installed or pheno_vendor directory is in the path."
        ) from e

# Provider configurations (mock interfaces for now - can be extended)
class DeploymentEnvironment:
    """Environment enumeration for deployments."""
    LOCAL = "local"
    PREVIEW = "preview"
    PRODUCTION = "production"

class DeploymentResult:
    """Deployment result wrapper."""
    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

class DeploymentProvider:
    """Base provider interface."""
    pass

class HealthCheckProvider:
    """Base health check interface."""
    pass

class ServerProvider:
    """Base server interface."""
    pass

class TunnelProvider:
    """Base tunnel interface."""
    pass

class ConfigurationProvider:
    """Base configuration interface."""
    pass

# Platform implementations (from pheno-sdk/deploy-kit)
try:
    # Try pheno-sdk if installed
    from pheno.kits.deploy.platforms.modern.vercel import VercelClient as VercelDeploymentProvider
    HTTPHealthCheckProvider = object  # Will be defined in atoms layer
    VercelConfigProvider = object  # Will be defined in atoms layer
    AdvancedHealthChecker = object  # Will be defined in atoms layer
except ImportError:
    try:
        # Fall back to vendored version
        from pheno_vendor.deploy_kit.platforms.modern.vercel import VercelClient as VercelDeploymentProvider
        HTTPHealthCheckProvider = object  # Will be defined in atoms layer
        VercelConfigProvider = object  # Will be defined in atoms layer
        AdvancedHealthChecker = object  # Will be defined in atoms layer
    except ImportError:
        # Final fallback - define minimal mock classes
        class VercelDeploymentProvider:
            pass
        class HTTPHealthCheckProvider:
            pass
        class VercelConfigProvider:
            pass
        class AdvancedHealthChecker:
            pass

# Atoms-specific implementations (stays in atoms_mcp-old)
from .atoms import (
    AtomsDeploymentConfig,
    AtomsServerManager,
    AtomsVercelDeployer,
    deploy_atoms_to_vercel,
    start_atoms_server,
)

__all__ = [
    # Base abstractions (from pheno-sdk/deploy-kit)
    "DeploymentEnvironment",
    "DeploymentStatus",
    "DeploymentConfig",
    "DeploymentResult",
    "DeploymentProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "ConfigurationProvider",

    # Platform implementations (from pheno-sdk/deploy-kit)
    "VercelDeploymentProvider",
    "VercelConfigProvider",
    "HTTPHealthCheckProvider",
    "AdvancedHealthChecker",

    # Atoms-specific (stays in atoms_mcp-old)
    "AtomsDeploymentConfig",
    "AtomsVercelDeployer",
    "deploy_atoms_to_vercel",
    "AtomsServerManager",
    "start_atoms_server",
]

