# Migration Guide: lib/ to pheno-sdk

## Overview

This guide explains how to migrate the framework-agnostic components from `atoms_mcp-old/lib/` to `pheno-sdk/deploy-kit/`.

## What to Migrate

### ✅ Migrate to pheno-sdk

These are framework-agnostic and should be moved:

```
lib/base/              → pheno-sdk/deploy-kit/base/
lib/platforms/         → pheno-sdk/deploy-kit/platforms/
```

### ❌ Keep in atoms_mcp-old

These are Atoms-specific and should stay:

```
lib/atoms/             → Stays in atoms_mcp-old
lib/deployment.py      → Legacy, can be removed after migration
lib/server_manager.py  → Legacy, can be removed after migration
```

## Migration Steps

### Step 1: Prepare pheno-sdk

```bash
cd ../pheno-sdk/deploy-kit

# Create directory structure
mkdir -p deploy_kit/base
mkdir -p deploy_kit/platforms
```

### Step 2: Copy Base Classes

```bash
# Copy base abstractions
cp ../../atoms_mcp-old/lib/base/deployment.py \
   deploy_kit/base/deployment.py

# Create __init__.py
cat > deploy_kit/base/__init__.py << 'EOF'
"""
Base Deployment Abstractions

Framework-agnostic interfaces for deployment operations.
"""

from .deployment import (
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

__all__ = [
    "DeploymentEnvironment",
    "DeploymentStatus",
    "DeploymentConfig",
    "DeploymentResult",
    "DeploymentProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "ConfigurationProvider",
]
EOF
```

### Step 3: Copy Platform Implementations

```bash
# Copy Vercel implementation
cp ../../atoms_mcp-old/lib/platforms/vercel.py \
   deploy_kit/platforms/vercel.py

# Copy HTTP health check
cp ../../atoms_mcp-old/lib/platforms/http_health.py \
   deploy_kit/platforms/http_health.py

# Create __init__.py
cat > deploy_kit/platforms/__init__.py << 'EOF'
"""
Platform Implementations

Platform-specific implementations of deployment interfaces.
"""

from .vercel import VercelDeploymentProvider, VercelConfigProvider
from .http_health import HTTPHealthCheckProvider, AdvancedHealthChecker

__all__ = [
    "VercelDeploymentProvider",
    "VercelConfigProvider",
    "HTTPHealthCheckProvider",
    "AdvancedHealthChecker",
]
EOF
```

### Step 4: Update pheno-sdk deploy_kit/__init__.py

```bash
cat > deploy_kit/__init__.py << 'EOF'
"""
Deploy Kit - Universal Deployment Toolkit

Provides framework-agnostic deployment abstractions and
platform-specific implementations.
"""

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

from .platforms import (
    VercelDeploymentProvider,
    VercelConfigProvider,
    HTTPHealthCheckProvider,
    AdvancedHealthChecker,
)

__all__ = [
    # Base
    "DeploymentEnvironment",
    "DeploymentStatus",
    "DeploymentConfig",
    "DeploymentResult",
    "DeploymentProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "ConfigurationProvider",
    
    # Platforms
    "VercelDeploymentProvider",
    "VercelConfigProvider",
    "HTTPHealthCheckProvider",
    "AdvancedHealthChecker",
]
EOF
```

### Step 5: Update Atoms Imports

Update `atoms_mcp-old/lib/atoms/deployment.py`:

```python
# Before
from ..base.deployment import (
    DeploymentConfig,
    DeploymentEnvironment,
    DeploymentResult,
)
from ..platforms.vercel import VercelDeploymentProvider, VercelConfigProvider
from ..platforms.http_health import HTTPHealthCheckProvider

# After
from deploy_kit.base import (
    DeploymentConfig,
    DeploymentEnvironment,
    DeploymentResult,
)
from deploy_kit.platforms.vercel import VercelDeploymentProvider, VercelConfigProvider
from deploy_kit.platforms.http_health import HTTPHealthCheckProvider
```

Update `atoms_mcp-old/lib/atoms/server.py`:

```python
# No changes needed - this file doesn't import from base/platforms
```

### Step 6: Update atoms_mcp-old/lib/__init__.py

```python
"""
Atoms MCP Library

Uses pheno-sdk/deploy-kit for base functionality.
"""

# Import from pheno-sdk
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

from deploy_kit.platforms import (
    VercelDeploymentProvider,
    VercelConfigProvider,
    HTTPHealthCheckProvider,
    AdvancedHealthChecker,
)

# Atoms-specific implementations
from .atoms import (
    AtomsDeploymentConfig,
    AtomsVercelDeployer,
    deploy_atoms_to_vercel,
    AtomsServerManager,
    start_atoms_server,
)

__all__ = [
    # From pheno-sdk
    "DeploymentEnvironment",
    "DeploymentStatus",
    "DeploymentConfig",
    "DeploymentResult",
    "DeploymentProvider",
    "HealthCheckProvider",
    "ServerProvider",
    "TunnelProvider",
    "ConfigurationProvider",
    "VercelDeploymentProvider",
    "VercelConfigProvider",
    "HTTPHealthCheckProvider",
    "AdvancedHealthChecker",
    
    # Atoms-specific
    "AtomsDeploymentConfig",
    "AtomsVercelDeployer",
    "deploy_atoms_to_vercel",
    "AtomsServerManager",
    "start_atoms_server",
]
```

### Step 7: Remove Migrated Files from atoms_mcp-old

```bash
cd ../../atoms_mcp-old

# Remove migrated directories
rm -rf lib/base/
rm -rf lib/platforms/

# Remove legacy files (optional)
rm lib/deployment.py
rm lib/server_manager.py
rm lib/__init__.py.backup
```

### Step 8: Update atoms_mcp-old requirements.txt

```bash
# Add deploy-kit dependency
echo "-e ../pheno-sdk/deploy-kit" >> requirements.txt
```

### Step 9: Test Migration

```bash
# Test imports
python -c "from deploy_kit.base import DeploymentProvider; print('✅ Base imports work')"
python -c "from deploy_kit.platforms import VercelDeploymentProvider; print('✅ Platform imports work')"
python -c "from lib.atoms import deploy_atoms_to_vercel; print('✅ Atoms imports work')"

# Test CLI
./atoms --help
./atoms deploy --help
```

## Verification Checklist

- [ ] pheno-sdk/deploy-kit/base/ created
- [ ] pheno-sdk/deploy-kit/platforms/ created
- [ ] All files copied correctly
- [ ] __init__.py files created
- [ ] Atoms imports updated
- [ ] atoms_mcp-old/lib/base/ removed
- [ ] atoms_mcp-old/lib/platforms/ removed
- [ ] requirements.txt updated
- [ ] All imports work
- [ ] CLI still works
- [ ] Tests pass

## Rollback Plan

If migration fails:

```bash
cd atoms_mcp-old

# Restore from backup
git restore lib/base/
git restore lib/platforms/
git restore lib/__init__.py
git restore lib/atoms/deployment.py
git restore lib/atoms/server.py
```

## Benefits After Migration

### ✅ Reusable Components

Other projects can use deploy-kit:

```python
# In any project
from deploy_kit.base import DeploymentConfig
from deploy_kit.platforms import VercelDeploymentProvider

config = DeploymentConfig(...)
provider = VercelDeploymentProvider(config)
result = provider.deploy()
```

### ✅ Centralized Maintenance

Updates to deployment logic benefit all projects:

```bash
# Update in pheno-sdk
cd pheno-sdk/deploy-kit
git pull

# All projects using deploy-kit get updates
```

### ✅ Consistent Interface

All projects use same deployment interface:

```python
# Project A
from deploy_kit.platforms import VercelDeploymentProvider

# Project B
from deploy_kit.platforms import VercelDeploymentProvider

# Same interface, different configs
```

## Post-Migration

### Update Documentation

- [ ] Update ARCHITECTURE.md
- [ ] Update README.md
- [ ] Update deployment guides
- [ ] Add deploy-kit to pheno-sdk docs

### Announce Changes

- [ ] Notify team of migration
- [ ] Update onboarding docs
- [ ] Create migration announcement

### Monitor

- [ ] Watch for import errors
- [ ] Monitor deployment success rate
- [ ] Collect feedback from team

## Summary

This migration:

1. **Extracts** framework-agnostic code to pheno-sdk
2. **Keeps** Atoms-specific code in atoms_mcp-old
3. **Maintains** backward compatibility
4. **Enables** reuse across projects
5. **Simplifies** maintenance

The result is a clean separation between:
- **pheno-sdk/deploy-kit**: Reusable deployment framework
- **atoms_mcp-old/lib/atoms**: Atoms-specific implementations

