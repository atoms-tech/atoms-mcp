#!/usr/bin/env python3
"""
Migrate base and platform layers from atoms_mcp-old to pheno-sdk/deploy-kit

This script:
1. Copies lib/base/ → pheno-sdk/deploy-kit/deploy_kit/base/
2. Copies lib/platforms/ → pheno-sdk/deploy-kit/deploy_kit/platforms/atoms/
3. Updates imports in atoms_mcp-old to use deploy_kit
4. Creates migration documentation
"""

import shutil
import sys
from pathlib import Path


class PhenoSDKMigrator:
    """Migrates atoms_mcp libraries to pheno-sdk."""

    def __init__(self):
        self.atoms_root = Path(__file__).parent
        self.pheno_sdk_root = self.atoms_root.parent / "pheno-sdk"
        self.deploy_kit_root = self.pheno_sdk_root / "deploy-kit" / "deploy_kit"

        # Source paths
        self.lib_base = self.atoms_root / "lib" / "base"
        self.lib_platforms = self.atoms_root / "lib" / "platforms"

        # Destination paths
        self.deploy_kit_base = self.deploy_kit_root / "base"
        self.deploy_kit_platforms_atoms = self.deploy_kit_root / "platforms" / "atoms"

    def check_prerequisites(self) -> bool:
        """Check if all required paths exist."""
        print("🔍 Checking prerequisites...")

        checks = [
            (self.pheno_sdk_root, "pheno-sdk root"),
            (self.deploy_kit_root, "deploy-kit"),
            (self.lib_base, "lib/base"),
            (self.lib_platforms, "lib/platforms"),
        ]

        all_good = True
        for path, name in checks:
            if path.exists():
                print(f"   ✅ {name}: {path}")
            else:
                print(f"   ❌ {name} not found: {path}")
                all_good = False

        return all_good

    def copy_base_layer(self) -> bool:
        """Copy lib/base/ to deploy-kit/deploy_kit/base/."""
        print("\n📦 Copying base layer...")

        try:
            # Remove existing if present
            if self.deploy_kit_base.exists():
                print(f"   🧹 Removing existing {self.deploy_kit_base}")
                shutil.rmtree(self.deploy_kit_base)

            # Copy
            print(f"   📁 Copying {self.lib_base} → {self.deploy_kit_base}")
            shutil.copytree(self.lib_base, self.deploy_kit_base)

            # Count files
            py_files = list(self.deploy_kit_base.rglob("*.py"))
            print(f"   ✅ Copied {len(py_files)} Python files")

            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def copy_platforms_layer(self) -> bool:
        """Copy lib/platforms/ to deploy-kit/deploy_kit/platforms/atoms/."""
        print("\n📦 Copying platforms layer...")

        try:
            # Create platforms directory if it doesn't exist
            platforms_dir = self.deploy_kit_root / "platforms"
            platforms_dir.mkdir(exist_ok=True)

            # Create __init__.py if it doesn't exist
            platforms_init = platforms_dir / "__init__.py"
            if not platforms_init.exists():
                platforms_init.write_text('"""Platform-specific implementations."""\n')

            # Remove existing atoms platform if present
            if self.deploy_kit_platforms_atoms.exists():
                print(f"   🧹 Removing existing {self.deploy_kit_platforms_atoms}")
                shutil.rmtree(self.deploy_kit_platforms_atoms)

            # Copy
            print(f"   📁 Copying {self.lib_platforms} → {self.deploy_kit_platforms_atoms}")
            shutil.copytree(self.lib_platforms, self.deploy_kit_platforms_atoms)

            # Count files
            py_files = list(self.deploy_kit_platforms_atoms.rglob("*.py"))
            print(f"   ✅ Copied {len(py_files)} Python files")

            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def update_deploy_kit_init(self) -> bool:
        """Update deploy-kit __init__.py to export base and platforms."""
        print("\n📝 Updating deploy-kit __init__.py...")

        try:
            init_file = self.deploy_kit_root / "__init__.py"

            # Read existing content
            if init_file.exists():
                with open(init_file) as f:
                    content = f.read()
            else:
                content = '"""Deploy-kit - Deployment utilities."""\n\n'

            # Add exports if not already present
            exports_to_add = []

            if "from .base" not in content:
                exports_to_add.append("""
# Base abstractions
from .base.deployment import (
    DeploymentProvider,
    DeploymentConfig,
    DeploymentResult,
    HealthCheckProvider,
    ServerManager,
    TunnelProvider,
    Environment,
    DeploymentStatus,
)
""")

            if "from .platforms.atoms" not in content:
                exports_to_add.append("""
# Platform implementations
from .platforms.atoms.vercel import VercelDeploymentProvider
from .platforms.atoms.http_health import HTTPHealthCheckProvider, AdvancedHealthChecker
""")

            if exports_to_add:
                content += "\n".join(exports_to_add)

                with open(init_file, "w") as f:
                    f.write(content)

                print(f"   ✅ Updated {init_file}")
            else:
                print("   ℹ️  Already up to date")

            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def create_migration_doc(self) -> bool:
        """Create migration documentation in pheno-sdk."""
        print("\n📚 Creating migration documentation...")

        try:
            doc_path = self.pheno_sdk_root / "deploy-kit" / "ATOMS_MIGRATION.md"

            doc_content = """# Atoms MCP Migration to Deploy-Kit

## Overview

This document describes the migration of deployment abstractions from atoms_mcp-old to pheno-sdk/deploy-kit.

## What Was Migrated

### Base Layer (`deploy_kit/base/`)

Abstract base classes for deployment, health checks, servers, and tunnels:

- `DeploymentProvider` - Abstract deployment provider
- `DeploymentConfig` - Deployment configuration
- `DeploymentResult` - Deployment result
- `HealthCheckProvider` - Health check provider
- `ServerManager` - Server management
- `TunnelProvider` - Tunnel provider
- `Environment` - Environment enum
- `DeploymentStatus` - Status enum

**100% platform-agnostic** - No Vercel, AWS, or Atoms-specific code.

### Platforms Layer (`deploy_kit/platforms/atoms/`)

Platform-specific implementations:

- `VercelDeploymentProvider` - Vercel deployment implementation
- `HTTPHealthCheckProvider` - HTTP-based health checks
- `AdvancedHealthChecker` - Advanced health checking features

**Platform-specific but app-agnostic** - Works for any app on Vercel.

## Usage

### In Atoms MCP

```python
# Old import (atoms_mcp-old/lib/)
from lib.base.deployment import DeploymentProvider
from lib.platforms.vercel import VercelDeploymentProvider

# New import (using pheno-sdk)
from deploy_kit.base.deployment import DeploymentProvider
from deploy_kit.platforms.atoms.vercel import VercelDeploymentProvider
```

### In Other Projects

```python
from deploy_kit.base.deployment import DeploymentProvider, DeploymentConfig
from deploy_kit.platforms.atoms.vercel import VercelDeploymentProvider

# Create custom deployment provider
class MyVercelDeployer(VercelDeploymentProvider):
    def get_deployment_config(self, env: Environment) -> DeploymentConfig:
        return DeploymentConfig(
            environment=env,
            domain="my-app.vercel.app",
            env_file=f".env.{{env.value}}",
        )

# Use it
deployer = MyVercelDeployer()
result = deployer.deploy(Environment.PREVIEW)
```

## Architecture

```
deploy-kit/
├── base/                    # Abstract base classes
│   ├── __init__.py
│   └── deployment.py        # All base abstractions
│
└── platforms/               # Platform implementations
    └── atoms/               # Atoms-specific platforms
        ├── __init__.py
        ├── vercel.py        # Vercel deployment
        └── http_health.py   # HTTP health checks
```

## Benefits

1. **Reusable** - Any project can use these abstractions
2. **Extensible** - Easy to add new platforms (AWS, GCP, etc.)
3. **Testable** - Each layer can be tested independently
4. **Type-Safe** - Full type hints throughout
5. **Well-Documented** - Clear API documentation

## Next Steps

1. Update atoms_mcp-old to import from deploy_kit
2. Remove lib/base/ and lib/platforms/ from atoms_mcp-old
3. Test deployment in atoms_mcp-old
4. Use in other projects

## Migration Date

{migration_date}

## Migrated By

Automated migration script
"""

            from datetime import datetime
            doc_content = doc_content.format(
                migration_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            with open(doc_path, "w") as f:
                f.write(doc_content)

            print(f"   ✅ Created {doc_path}")
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def run(self) -> bool:
        """Run the migration."""
        print("\n" + "=" * 70)
        print("  Migrating Atoms MCP Libraries to Pheno-SDK")
        print("=" * 70 + "\n")

        if not self.check_prerequisites():
            print("\n❌ Prerequisites check failed")
            return False

        steps = [
            ("Copy base layer", self.copy_base_layer),
            ("Copy platforms layer", self.copy_platforms_layer),
            ("Update deploy-kit __init__.py", self.update_deploy_kit_init),
            ("Create migration documentation", self.create_migration_doc),
        ]

        for step_name, step_fn in steps:
            if not step_fn():
                print(f"\n❌ Failed at: {step_name}")
                return False

        print("\n" + "=" * 70)
        print("✅ Migration Complete!")
        print("=" * 70 + "\n")

        print("📋 Next Steps:")
        print("   1. Update atoms_mcp-old imports to use deploy_kit")
        print("   2. Test deployment in atoms_mcp-old")
        print("   3. Remove lib/base/ and lib/platforms/ from atoms_mcp-old")
        print("   4. Commit changes to pheno-sdk")
        print()

        return True


def main():
    """Main entry point."""
    migrator = PhenoSDKMigrator()
    success = migrator.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

