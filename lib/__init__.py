"""
Atoms MCP Library

Modular, framework-agnostic deployment and server management.

Architecture:
- lib/base/         → Abstract interfaces (move to pheno-sdk/deploy-kit/base/)
- lib/platforms/    → Platform implementations (move to pheno-sdk/deploy-kit/platforms/)
- lib/atoms/        → Atoms-specific implementations (stays in atoms_mcp-old)

This design allows easy extraction to pheno-sdk while keeping
Atoms-specific logic in the atoms_mcp-old repository.
"""

# Base abstractions (pheno-sdk/deploy-kit/base/)
from .base import (
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

# Platform implementations (pheno-sdk/deploy-kit/platforms/)
from .platforms import (
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

