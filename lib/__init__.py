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

# Base abstractions (from pheno-sdk/deploy-kit)
from deploy_kit.base import (
    DeploymentEnvironment,
    DeploymentStatus,
    DeploymentConfig,
    DeploymentResult,
    DeploymentProvider,
    HealthCheckProvider,
    ServerProvider,
    TunnelProvider,
    ConfigurationProvider,
)

# Platform implementations (from pheno-sdk/deploy-kit)
from deploy_kit.platforms import (
    VercelDeploymentProvider,
    VercelConfigProvider,
    HTTPHealthCheckProvider,
    AdvancedHealthChecker,
)

# Atoms-specific implementations (stays in atoms_mcp-old)
from .atoms import (
    AtomsDeploymentConfig,
    AtomsVercelDeployer,
    deploy_atoms_to_vercel,
    AtomsServerManager,
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

