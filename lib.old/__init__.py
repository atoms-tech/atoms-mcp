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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    DeploymentConfig = Any  # type: ignore[assignment, misc]
    DeploymentState = Any  # type: ignore[assignment, misc]
    DeploymentStatus = Any  # type: ignore[assignment, misc]
else:
    try:
        # Try pheno-sdk if installed
        from pheno.deployment import (
            DeploymentConfig,
            DeploymentState,
            DeploymentStatus,
        )
    except ImportError:
        # Fallback: define minimal stubs
        class DeploymentConfig:  # type: ignore[no-redef]
            pass

        class DeploymentState:  # type: ignore[no-redef]
            pass

        class DeploymentStatus:  # type: ignore[no-redef]
            pass

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
if TYPE_CHECKING:
    from typing import Any
    VercelConfigProvider = Any  # type: ignore[assignment, misc]
    AdvancedHealthChecker = Any  # type: ignore[assignment, misc]
else:
    try:
        from pheno.kits.deploy.platforms.vercel import VercelClient as VercelDeploymentProvider

        from .atoms.infrastructure.types import HTTPHealthCheckProvider

        # Placeholder objects - will be defined properly if needed
        VercelConfigProvider = object  # Defined in atoms layer when needed
        AdvancedHealthChecker = object  # Defined in atoms layer when needed
    except ImportError:  # pragma: no cover - optional dependency
        # Final fallback - import lightweight stubs so the module continues to load
        from .atoms.infrastructure.types import HTTPHealthCheckProvider, VercelDeploymentProvider

        class VercelConfigProvider:  # type: ignore[no-redef]
            """Fallback configuration provider when pheno-sdk is unavailable."""

        class AdvancedHealthChecker:  # type: ignore[no-redef]
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
