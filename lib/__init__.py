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

# Atoms-specific implementations (stays in atoms_mcp-old)

# Core types (from pheno-sdk deployment module)
try:
    # Try pheno-sdk if installed
    from pheno.deployment import (
        DeploymentConfig,
        DeploymentState,
        DeploymentStatus,
    )
except ImportError:
    try:
        # Fallback: define minimal stubs
        class DeploymentConfig:
            pass
        class DeploymentState:
            pass
        class DeploymentStatus:
            pass
    except Exception as e:
        raise ImportError(
            "Could not import deployment types from pheno-sdk. "
            "Make sure pheno-sdk is properly installed."
        ) from e

from .atoms import (
    AtomsDeploymentConfig,
    AtomsServerManager,
    AtomsVercelDeployer,
    deploy_atoms_to_vercel,
    start_atoms_server,
)


# Provider configurations (mock interfaces for now - can be extended)
# Import deployment types from infrastructure module
from .atoms.infrastructure.types import DeploymentEnvironment, DeploymentResult

class DeploymentProvider:
    """Base provider interface."""

class HealthCheckProvider:
    """Base health check interface."""

class ServerProvider:
    """Base server interface."""

class TunnelProvider:
    """Base tunnel interface."""

class ConfigurationProvider:
    """Base configuration interface."""

# Platform implementations (from pheno-sdk/deploy-kit)
try:
    from pheno.kits.deploy.platforms.vercel import VercelClient as VercelDeploymentProvider
    from .atoms.infrastructure.types import HTTPHealthCheckProvider
    VercelConfigProvider = object  # Defined in atoms layer when needed
    AdvancedHealthChecker = object  # Defined in atoms layer when needed
except ImportError:  # pragma: no cover - optional dependency
    # Final fallback - import lightweight stubs so the module continues to load
    from .atoms.infrastructure.types import VercelDeploymentProvider, HTTPHealthCheckProvider

    class VercelConfigProvider:
        """Fallback configuration provider when pheno-sdk is unavailable."""

    class AdvancedHealthChecker:
        """Fallback health checker when pheno-sdk is unavailable."""

__all__ = [
    "AdvancedHealthChecker",
    # Atoms-specific (stays in atoms_mcp-old)
    "AtomsDeploymentConfig",
    "AtomsServerManager",
    "AtomsVercelDeployer",
    "ConfigurationProvider",
    "DeploymentConfig",
    # Base abstractions (from pheno-sdk/deploy-kit)
    "DeploymentEnvironment",
    "DeploymentProvider",
    "DeploymentResult",
    "DeploymentStatus",
    "HTTPHealthCheckProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "VercelConfigProvider",
    # Platform implementations (from pheno-sdk/deploy-kit)
    "VercelDeploymentProvider",
    "deploy_atoms_to_vercel",
    "start_atoms_server",
]
