"""
Vendor Manager - Pheno-SDK Package Vendoring

Handles copying pheno-sdk packages into pheno_vendor/ for production deployments.
Replaces scripts/vendor-pheno-sdk.sh with a proper Python library.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Package configuration
PACKAGES = [
    "mcp-QA",
    "pydevkit",
    "db-kit",
    "deploy-kit",
    "observability-kit",
    "cli-builder-kit",
    "filewatch-kit",
    "authkit-client",
    "adapter-kit",
    "vector-kit",
    "workflow-kit",
]

PACKAGE_NAMES = {
    "mcp-QA": "mcp_qa",
    "pydevkit": "pydevkit",
    "db-kit": "db_kit",
    "deploy-kit": "deploy_kit",
    "observability-kit": "observability_kit",
    "cli-builder-kit": "cli_builder",
    "filewatch-kit": "filewatch_kit",
    "authkit-client": "authkit_client",
    "adapter-kit": "adapter_kit",
    "vector-kit": "vector_kit",
    "workflow-kit": "workflow_kit",
}


class VendorManager:
    """Manages vendoring of pheno-sdk packages."""

    def __init__(self, project_root: Optional[Path] = None, pheno_sdk_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.pheno_sdk_root = pheno_sdk_root or self.project_root.parent / "pheno-sdk"
        self.vendor_dir = self.project_root / "pheno_vendor"

    def check_prerequisites(self) -> bool:
        """Check if pheno-sdk exists."""
        if not self.pheno_sdk_root.exists():
            print(f"❌ Pheno-SDK not found at: {self.pheno_sdk_root}")
            print("   Set PHENO_SDK_ROOT environment variable or ensure pheno-sdk is in expected location")
            return False
        print(f"✅ Pheno-SDK found at: {self.pheno_sdk_root}")
        return True

    def clean_vendor(self) -> None:
        """Remove existing vendor directory."""
        if self.vendor_dir.exists():
            print("🧹 Cleaning existing vendor directory...")
            shutil.rmtree(self.vendor_dir)
            print("✅ Vendor directory cleaned")

    def create_vendor_structure(self) -> None:
        """Create vendor directory with __init__.py."""
        print("📁 Creating vendor directory structure...")
        self.vendor_dir.mkdir(parents=True, exist_ok=True)

        init_file = self.vendor_dir / "__init__.py"
        init_file.write_text('''"""
Vendored pheno-sdk packages for production deployment.

This directory contains copies of pheno-sdk packages to avoid
dependency on relative paths in production environments.
"""

__version__ = "1.0.0"
''')
        print("✅ Vendor structure created")

    def copy_package(self, pkg_dir: str) -> bool:
        """Copy a single package to vendor directory."""
        pkg_name = PACKAGE_NAMES.get(pkg_dir)
        if not pkg_name:
            print(f"⚠️  Unknown package: {pkg_dir}")
            return False

        source_path = self.pheno_sdk_root / pkg_dir
        dest_path = self.vendor_dir / pkg_name

        if not source_path.exists():
            print(f"⚠️  Package not found: {pkg_dir} (skipping)")
            return False

        print(f"📦 Vendoring {pkg_dir} -> {pkg_name}...")

        # Check for setup.py or pyproject.toml
        if not (source_path / "setup.py").exists() and not (source_path / "pyproject.toml").exists():
            print(f"⚠️  No setup.py or pyproject.toml found for {pkg_dir} (skipping)")
            return False

        # Find the actual Python package directory
        python_pkg_path = source_path / pkg_name
        if not python_pkg_path.exists():
            python_pkg_path = source_path / "src" / pkg_name
            if not python_pkg_path.exists():
                python_pkg_path = source_path

        # Copy the package
        if python_pkg_path.exists() and python_pkg_path != source_path:
            shutil.copytree(python_pkg_path, dest_path, dirs_exist_ok=True)
        else:
            dest_path.mkdir(parents=True, exist_ok=True)
            if (source_path / pkg_name).exists():
                shutil.copytree(source_path / pkg_name, dest_path, dirs_exist_ok=True)
            else:
                # Copy Python files and subdirectories
                for item in source_path.iterdir():
                    if item.suffix == ".py":
                        shutil.copy2(item, dest_path)
                    elif item.is_dir() and not item.name.startswith(".") and item.name not in ["tests", "docs", "examples"]:
                        shutil.copytree(item, dest_path / item.name, dirs_exist_ok=True)

        # Copy metadata files
        for meta_file in ["setup.py", "setup.cfg", "pyproject.toml", "README.md", "LICENSE"]:
            meta_path = source_path / meta_file
            if meta_path.exists():
                shutil.copy2(meta_path, dest_path)

        # Clean up unwanted files
        self._cleanup_package(dest_path)

        print(f"✅ Vendored {pkg_dir}")
        return True

    def handle_kinfra(self) -> bool:
        """Handle KInfra package vendoring."""
        kinfra_source = self.pheno_sdk_root / "KInfra" / "libraries" / "python"
        kinfra_dest = self.vendor_dir / "kinfra"

        # Handle symlink
        kinfra_root = self.pheno_sdk_root / "KInfra"
        if kinfra_root.is_symlink():
            real_kinfra = kinfra_root.resolve()
            kinfra_source = real_kinfra / "libraries" / "python"

        if not kinfra_source.exists():
            print("⚠️  KInfra not found (skipping)")
            return False

        print("📦 Vendoring KInfra...")

        kinfra_dest.mkdir(parents=True, exist_ok=True)

        # Copy KInfra package
        if (kinfra_source / "kinfra").exists():
            shutil.copytree(kinfra_source / "kinfra", kinfra_dest, dirs_exist_ok=True)
        else:
            for item in kinfra_source.iterdir():
                if item.is_file() and item.suffix == ".py":
                    shutil.copy2(item, kinfra_dest)
                elif item.is_dir() and not item.name.startswith("."):
                    shutil.copytree(item, kinfra_dest / item.name, dirs_exist_ok=True)

        # Copy metadata
        for meta_file in ["setup.py", "setup.cfg", "pyproject.toml", "README.md", "LICENSE"]:
            meta_path = kinfra_source / meta_file
            if meta_path.exists():
                shutil.copy2(meta_path, kinfra_dest)

        self._cleanup_package(kinfra_dest)

        print("✅ Vendored KInfra")
        return True

    def _cleanup_package(self, package_path: Path) -> None:
        """Remove unwanted files from vendored package."""
        patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".pytest_cache",
            ".mypy_cache",
            "*.egg-info",
        ]

        for pattern in patterns:
            if "*" in pattern:
                for item in package_path.rglob(pattern):
                    if item.is_file():
                        item.unlink()
            else:
                for item in package_path.rglob(pattern):
                    if item.is_dir():
                        shutil.rmtree(item)

    def create_requirements_prod(self) -> None:
        """Generate requirements-prod.txt without editable installs."""
        print("📝 Creating requirements-prod.txt...")

        req_file = self.project_root / "requirements-prod.txt"
        dev_req = self.project_root / "requirements.txt"

        if not dev_req.exists():
            print("❌ requirements.txt not found")
            return

        header = """# ============================================================================
# Production Requirements for Atoms MCP
# ============================================================================
# This file uses VENDORED pheno-sdk packages from pheno_vendor/
# For development, use requirements.txt with editable installs
# Generated by lib/vendor_manager.py
# ============================================================================

"""

        # Filter out editable installs
        with open(dev_req) as f:
            lines = [
                line for line in f
                if not line.strip().startswith("-e") and "pheno-sdk" not in line
            ]

        with open(req_file, "w") as f:
            f.write(header)
            f.writelines(lines)

        print("✅ Created requirements-prod.txt")

    def create_sitecustomize(self) -> None:
        """Create sitecustomize.py to add vendor path."""
        print("📝 Creating sitecustomize.py...")

        sitecustomize = self.project_root / "sitecustomize.py"
        sitecustomize.write_text('''"""
Site customization to add vendored pheno-sdk packages to sys.path.
"""

import sys
from pathlib import Path

vendor_path = Path(__file__).parent / "pheno_vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.insert(0, str(vendor_path))
''')

        print("✅ Created sitecustomize.py")

    def verify_vendored_packages(self) -> Tuple[int, int]:
        """Verify vendored packages have Python files."""
        print("🔍 Verifying vendored packages...")

        success_count = 0
        error_count = 0

        for pkg_dir in PACKAGES:
            pkg_name = PACKAGE_NAMES[pkg_dir]
            pkg_path = self.vendor_dir / pkg_name

            if not pkg_path.exists():
                print(f"⚠️  Package not vendored: {pkg_name}")
                continue

            py_files = list(pkg_path.rglob("*.py"))
            if not py_files:
                print(f"❌ No Python files found in {pkg_name}")
                error_count += 1
            else:
                print(f"✅ Verified {pkg_name} ({len(py_files)} Python files)")
                success_count += 1

        # Check KInfra
        kinfra_path = self.vendor_dir / "kinfra"
        if kinfra_path.exists():
            py_files = list(kinfra_path.rglob("*.py"))
            if not py_files:
                print("❌ No Python files found in kinfra")
                error_count += 1
            else:
                print(f"✅ Verified kinfra ({len(py_files)} Python files)")
                success_count += 1

        return success_count, error_count

    def generate_manifest(self) -> None:
        """Generate manifest file with package info."""
        print("📋 Generating VENDOR_MANIFEST.txt...")

        manifest = self.vendor_dir / "VENDOR_MANIFEST.txt"
        lines = [
            "Pheno-SDK Vendored Packages Manifest (Atoms MCP)",
            f"Generated: {datetime.now()}",
            f"Source: {self.pheno_sdk_root}",
            "",
            "Packages:",
        ]

        for pkg_dir in PACKAGES:
            pkg_name = PACKAGE_NAMES[pkg_dir]
            pkg_path = self.vendor_dir / pkg_name

            if pkg_path.exists():
                files = len(list(pkg_path.rglob("*")))
                size = sum(f.stat().st_size for f in pkg_path.rglob("*") if f.is_file())
                size_mb = size / (1024 * 1024)
                lines.append(f"  - {pkg_name} ({files} files, {size_mb:.2f} MB)")

        kinfra_path = self.vendor_dir / "kinfra"
        if kinfra_path.exists():
            files = len(list(kinfra_path.rglob("*")))
            size = sum(f.stat().st_size for f in kinfra_path.rglob("*") if f.is_file())
            size_mb = size / (1024 * 1024)
            lines.append(f"  - kinfra ({files} files, {size_mb:.2f} MB)")

        total_size = sum(f.stat().st_size for f in self.vendor_dir.rglob("*") if f.is_file())
        total_mb = total_size / (1024 * 1024)
        lines.append("")
        lines.append(f"Total size: {total_mb:.2f} MB")

        manifest.write_text("\n".join(lines))
        print("✅ Generated manifest")

    def vendor_all(self, clean: bool = False) -> bool:
        """Vendor all packages."""
        print("\n" + "=" * 70)
        print("  Pheno-SDK Vendoring (Atoms MCP)")
        print("=" * 70 + "\n")

        if not self.check_prerequisites():
            return False

        if clean:
            self.clean_vendor()

        self.create_vendor_structure()

        # Vendor packages
        for pkg in PACKAGES:
            self.copy_package(pkg)

        self.handle_kinfra()
        self.create_requirements_prod()
        self.create_sitecustomize()
        self.generate_manifest()

        success, errors = self.verify_vendored_packages()

        print("\n" + "=" * 70)
        if errors == 0:
            print("✅ Vendoring complete!")
        else:
            print(f"⚠️  Vendoring complete with {errors} errors")
        print("=" * 70 + "\n")

        print(f"Vendored packages location: {self.vendor_dir}")
        print(f"Production requirements: {self.project_root / 'requirements-prod.txt'}")
        print()

        return errors == 0

