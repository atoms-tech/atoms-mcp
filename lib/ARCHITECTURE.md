# Library Architecture

## Overview

The `lib/` directory contains a modular, framework-agnostic deployment and server management system designed for easy extraction to pheno-sdk.

## Architecture Layers

```
lib/
├── base/           → Abstract interfaces (→ pheno-sdk/deploy-kit/base/)
├── platforms/      → Platform implementations (→ pheno-sdk/deploy-kit/platforms/)
├── atoms/          → Atoms-specific implementations (stays in atoms_mcp-old)
└── deployment.py   → Legacy compatibility (deprecated)
```

### Layer 1: Base Abstractions (`lib/base/`)

**Purpose:** Define framework-agnostic interfaces

**Location:** → `pheno-sdk/deploy-kit/base/`

**Files:**
- `deployment.py` - Abstract base classes for deployment, health checks, servers, tunnels

**Classes:**
- `DeploymentProvider` - Abstract deployment interface
- `HealthCheckProvider` - Abstract health check interface
- `ServerProvider` - Abstract server interface
- `TunnelProvider` - Abstract tunnel interface
- `ConfigurationProvider` - Abstract configuration interface

**Data Classes:**
- `DeploymentConfig` - Deployment configuration
- `DeploymentResult` - Deployment result
- `DeploymentEnvironment` - Environment enum
- `DeploymentStatus` - Status enum

**Example:**
```python
from lib.base import DeploymentProvider, DeploymentConfig, DeploymentResult

class MyDeploymentProvider(DeploymentProvider):
    def deploy(self) -> DeploymentResult:
        # Platform-specific implementation
        pass
```

### Layer 2: Platform Implementations (`lib/platforms/`)

**Purpose:** Implement base interfaces for specific platforms

**Location:** → `pheno-sdk/deploy-kit/platforms/`

**Files:**
- `vercel.py` - Vercel deployment implementation
- `http_health.py` - HTTP health check implementation

**Classes:**
- `VercelDeploymentProvider` - Vercel-specific deployment
- `VercelConfigProvider` - Vercel configuration helpers
- `HTTPHealthCheckProvider` - HTTP health checks
- `AdvancedHealthChecker` - Advanced health checking

**Example:**
```python
from lib.platforms import VercelDeploymentProvider
from lib.base import DeploymentConfig, DeploymentEnvironment

config = DeploymentConfig(
    environment=DeploymentEnvironment.PRODUCTION,
    project_root=Path.cwd()
)

provider = VercelDeploymentProvider(config)
result = provider.deploy()
```

### Layer 3: Atoms-Specific (`lib/atoms/`)

**Purpose:** Atoms MCP specific implementations

**Location:** Stays in `atoms_mcp-old`

**Files:**
- `deployment.py` - Atoms deployment logic
- `server.py` - Atoms server management

**Classes:**
- `AtomsDeploymentConfig` - Atoms-specific config (domains, env files)
- `AtomsVercelDeployer` - Atoms-specific Vercel deployer
- `AtomsServerManager` - Atoms-specific server manager

**Functions:**
- `deploy_atoms_to_vercel()` - Convenience function for CLI
- `start_atoms_server()` - Convenience function for CLI

**Example:**
```python
from lib.atoms import deploy_atoms_to_vercel

# Deploy Atoms MCP to Vercel
result = deploy_atoms_to_vercel(
    environment="production",
    logger=my_logger
)
```

## Migration Path to Pheno-SDK

### Current State

```
atoms_mcp-old/
└── lib/
    ├── base/           # Abstract interfaces
    ├── platforms/      # Platform implementations
    └── atoms/          # Atoms-specific
```

### Target State

```
pheno-sdk/
└── deploy-kit/
    ├── base/           # Moved from atoms_mcp-old/lib/base/
    └── platforms/      # Moved from atoms_mcp-old/lib/platforms/

atoms_mcp-old/
└── lib/
    └── atoms/          # Stays here, uses pheno-sdk
```

### Migration Steps

1. **Copy base/ to pheno-sdk:**
   ```bash
   cp -r lib/base/ ../pheno-sdk/deploy-kit/base/
   ```

2. **Copy platforms/ to pheno-sdk:**
   ```bash
   cp -r lib/platforms/ ../pheno-sdk/deploy-kit/platforms/
   ```

3. **Update atoms/ imports:**
   ```python
   # Before
   from ..base.deployment import DeploymentProvider
   from ..platforms.vercel import VercelDeploymentProvider
   
   # After
   from deploy_kit.base import DeploymentProvider
   from deploy_kit.platforms.vercel import VercelDeploymentProvider
   ```

4. **Remove base/ and platforms/ from atoms_mcp-old:**
   ```bash
   rm -rf lib/base/ lib/platforms/
   ```

5. **Update lib/__init__.py:**
   ```python
   # Import from pheno-sdk instead
   from deploy_kit.base import *
   from deploy_kit.platforms import *
   from .atoms import *
   ```

## Design Principles

### 1. Framework-Agnostic Base Classes

All base classes are completely platform-agnostic:

```python
class DeploymentProvider(ABC):
    """Works with ANY deployment platform."""
    
    @abstractmethod
    def deploy(self) -> DeploymentResult:
        """Platform implements this."""
        pass
```

### 2. Platform-Specific Implementations

Platform classes implement base interfaces:

```python
class VercelDeploymentProvider(DeploymentProvider):
    """Vercel-specific implementation."""
    
    def deploy(self) -> DeploymentResult:
        # Vercel-specific logic
        subprocess.run(["vercel", "--prod"])
```

### 3. Application-Specific Wrappers

Application classes use platform implementations:

```python
class AtomsVercelDeployer:
    """Atoms-specific wrapper."""
    
    def __init__(self, environment):
        # Create Atoms-specific config
        config = AtomsDeploymentConfig.create_config(environment)
        
        # Use platform provider
        self.provider = VercelDeploymentProvider(config)
    
    def deploy(self):
        # Add Atoms-specific behavior
        result = self.provider.deploy()
        self._display_atoms_info(result)
        return result
```

## Usage Examples

### Example 1: Deploy Atoms to Vercel

```python
from lib.atoms import deploy_atoms_to_vercel

# Simple deployment
result = deploy_atoms_to_vercel("production")
```

### Example 2: Custom Deployment

```python
from lib.base import DeploymentConfig, DeploymentEnvironment
from lib.platforms import VercelDeploymentProvider

# Create custom config
config = DeploymentConfig(
    environment=DeploymentEnvironment.PRODUCTION,
    project_root=Path("/my/project"),
    domain="myapp.com"
)

# Deploy
provider = VercelDeploymentProvider(config)
result = provider.deploy()

if result.success:
    print(f"Deployed to {result.url}")
```

### Example 3: Health Check

```python
from lib.platforms import HTTPHealthCheckProvider

checker = HTTPHealthCheckProvider()

# Simple check
healthy = checker.check("https://myapp.com/health")

# Check with retries
healthy = checker.check_with_retries(
    url="https://myapp.com/health",
    max_retries=5,
    retry_delay=2
)
```

### Example 4: Start Atoms Server

```python
from lib.atoms import start_atoms_server

# Start server
exit_code = start_atoms_server(
    port=50002,
    verbose=True,
    no_tunnel=False
)
```

## Benefits

### ✅ Separation of Concerns

- **Base:** Pure abstractions, no platform code
- **Platforms:** Platform-specific, no app code
- **Atoms:** App-specific, uses base + platforms

### ✅ Easy to Test

Each layer can be tested independently:

```python
# Test base abstractions
class MockDeploymentProvider(DeploymentProvider):
    def deploy(self):
        return DeploymentResult(status=DeploymentStatus.SUCCESS)

# Test platform implementations
def test_vercel_deployment():
    config = DeploymentConfig(...)
    provider = VercelDeploymentProvider(config)
    result = provider.deploy()
    assert result.success

# Test Atoms-specific
def test_atoms_deployment():
    result = deploy_atoms_to_vercel("preview")
    assert result == 0
```

### ✅ Easy to Extend

Add new platforms without changing base or atoms:

```python
# Add AWS deployment
class AWSDeploymentProvider(DeploymentProvider):
    def deploy(self):
        # AWS-specific logic
        pass

# Use in Atoms
class AtomsAWSDeployer:
    def __init__(self):
        self.provider = AWSDeploymentProvider(...)
```

### ✅ Reusable Across Projects

Other projects can use base + platforms:

```python
# In another project
from deploy_kit.base import DeploymentConfig
from deploy_kit.platforms import VercelDeploymentProvider

# Use same platform code with different config
config = DeploymentConfig(
    environment=DeploymentEnvironment.PRODUCTION,
    domain="otherproject.com"
)

provider = VercelDeploymentProvider(config)
result = provider.deploy()
```

## Future Enhancements

### Additional Platforms

- [ ] AWS Lambda deployment provider
- [ ] Docker deployment provider
- [ ] Kubernetes deployment provider
- [ ] Netlify deployment provider

### Additional Features

- [ ] Deployment rollback automation
- [ ] Blue-green deployments
- [ ] Canary deployments
- [ ] Deployment metrics collection
- [ ] Deployment notifications (Slack, email)

### Integration with Other Kits

- [ ] Use observability-kit for metrics
- [ ] Use config-kit for configuration
- [ ] Use tui-kit for interactive deployments

## Summary

This architecture provides:

- **Clean separation** between abstractions, platforms, and applications
- **Easy migration** to pheno-sdk (just copy base/ and platforms/)
- **Reusable components** across projects
- **Testable layers** with clear boundaries
- **Extensible design** for new platforms and features

The design follows SOLID principles and makes it easy to extract reusable components to pheno-sdk while keeping Atoms-specific logic in atoms_mcp-old.

