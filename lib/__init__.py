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

# Base abstractions (from pheno-sdk/deploy-kit/base/)
from deploy_kit.base.deployment import (
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

# Platform implementations (from pheno-sdk/deploy-kit/platforms/)
from deploy_kit.platforms.atoms.vercel import (
    VercelDeploymentProvider,
    VercelConfigProvider,
)
from deploy_kit.platforms.atoms.http_health import (
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

# Legacy compatibility (deprecated, use atoms.* instead)
from .deployment import deploy_to_vercel, start_local_server

__all__ = [
    # Base abstractions (→ pheno-sdk)
    "DeploymentEnvironment",
    "DeploymentStatus",
    "DeploymentConfig",
    "DeploymentResult",
    "DeploymentProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "ConfigurationProvider",
    
    # Platform implementations (→ pheno-sdk)
    "VercelDeploymentProvider",
    "VercelConfigProvider",
    "HTTPHealthCheckProvider",
    "AdvancedHealthChecker",
    
    # Atoms-specific (stays here)
    "AtomsDeploymentConfig",
    "AtomsVercelDeployer",
    "deploy_atoms_to_vercel",
    "AtomsServerManager",
    "start_atoms_server",
    
    # Legacy (deprecated)
    "deploy_to_vercel",
    "start_local_server",
]

