"""
Deployment Checker - Pre-deployment validation

Generic, configurable deployment readiness checker.
Can be used by any project deploying to Vercel or other platforms.

This should eventually move to pheno-sdk/deploy-kit/
"""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class DeploymentCheck:
    """A single deployment check."""
    name: str
    check_fn: Callable[[], Tuple[bool, str]]
    severity: str = "error"  # "error" or "warning"
    fix_hint: Optional[str] = None


class DeploymentChecker:
    """Generic deployment readiness checker."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.errors = 0
        self.warnings = 0
    
    def check_directory_exists(self, path: str, name: str) -> Tuple[bool, str]:
        """Check if a directory exists."""
        dir_path = self.project_root / path
        if dir_path.exists() and dir_path.is_dir():
            # Count items
            items = [item for item in dir_path.iterdir() if not item.name.startswith('.') and item.name != '__pycache__']
            return True, f"{path}/ exists with {len(items)} items"
        return False, f"{path}/ not found"
    
    def check_file_exists(self, path: str, name: str) -> Tuple[bool, str]:
        """Check if a file exists."""
        file_path = self.project_root / path
        if file_path.exists() and file_path.is_file():
            return True, f"{path} exists"
        return False, f"{path} not found"
    
    def check_file_executable(self, path: str, name: str) -> Tuple[bool, str]:
        """Check if a file is executable."""
        file_path = self.project_root / path
        if not file_path.exists():
            return False, f"{path} not found"
        if os.access(file_path, os.X_OK):
            return True, f"{path} is executable"
        return False, f"{path} is not executable"
    
    def check_file_not_contains(self, path: str, pattern: str, name: str) -> Tuple[bool, str]:
        """Check that a file doesn't contain a pattern."""
        file_path = self.project_root / path
        if not file_path.exists():
            return False, f"{path} not found"
        
        with open(file_path) as f:
            content = f.read()
        
        if re.search(pattern, content, re.MULTILINE):
            return False, f"{path} contains forbidden pattern: {pattern}"
        return True, f"{path} doesn't contain {pattern}"
    
    def check_file_contains(self, path: str, pattern: str, name: str) -> Tuple[bool, str]:
        """Check that a file contains a pattern."""
        file_path = self.project_root / path
        if not file_path.exists():
            return False, f"{path} not found"
        
        with open(file_path) as f:
            content = f.read()
        
        if re.search(pattern, content, re.MULTILINE):
            return True, f"{path} contains {pattern}"
        return False, f"{path} doesn't contain {pattern}"
    
    def check_git_tracked(self, path: str, name: str) -> Tuple[bool, str]:
        """Check if a file/directory is tracked by git."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", path],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, f"{path} is tracked by git"
            return False, f"{path} is not tracked by git"
        except FileNotFoundError:
            return False, "git not found"
    
    def check_no_uncommitted_changes(self) -> Tuple[bool, str]:
        """Check for uncommitted changes."""
        try:
            # Check if in git repo
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.project_root,
                capture_output=True,
                check=True
            )
            
            # Check for changes
            result = subprocess.run(
                ["git", "diff", "--quiet"],
                cwd=self.project_root,
                capture_output=True
            )
            
            result2 = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=self.project_root,
                capture_output=True
            )
            
            if result.returncode == 0 and result2.returncode == 0:
                return True, "No uncommitted changes"
            return False, "Uncommitted changes detected"
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False, "Not a git repository"
    
    def run_check(self, check: DeploymentCheck) -> None:
        """Run a single check and print result."""
        passed, message = check.check_fn()
        
        if passed:
            print(f"   ✅ {message}")
        else:
            icon = "❌" if check.severity == "error" else "⚠️"
            print(f"   {icon} {message}")
            if check.fix_hint:
                print(f"      {check.fix_hint}")
            
            if check.severity == "error":
                self.errors += 1
            else:
                self.warnings += 1
    
    def run_all(self, checks: List[DeploymentCheck]) -> Tuple[int, int]:
        """Run all checks and return (errors, warnings)."""
        print("\n🔍 Deployment Readiness Check")
        print("=" * 70)
        print()
        
        # Group checks by category
        categories: Dict[str, List[DeploymentCheck]] = {}
        for check in checks:
            # Extract category from check name (before first ':')
            if ':' in check.name:
                category, _ = check.name.split(':', 1)
            else:
                category = "General"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(check)
        
        # Run checks by category
        for category, category_checks in categories.items():
            print(f"{category}")
            for check in category_checks:
                self.run_check(check)
            print()
        
        # Summary
        print("=" * 70)
        print("📊 Summary")
        print("=" * 70)
        print()
        
        if self.errors == 0 and self.warnings == 0:
            print("✅ All checks passed!")
            print()
            return 0, 0
        elif self.errors == 0:
            print(f"⚠️  {self.warnings} warning(s) found")
            print()
            print("You can deploy, but some issues should be addressed.")
            print()
            return 0, self.warnings
        else:
            print(f"❌ {self.errors} error(s) and {self.warnings} warning(s) found")
            print()
            print("Fix errors before deploying.")
            print()
            return self.errors, self.warnings


def create_vercel_deployment_checks(project_root: Optional[Path] = None) -> List[DeploymentCheck]:
    """Create standard Vercel deployment checks."""
    checker = DeploymentChecker(project_root)
    
    return [
        # Vendored packages
        DeploymentCheck(
            name="📦 Vendored packages: Directory exists",
            check_fn=lambda: checker.check_directory_exists("pheno_vendor", "pheno_vendor"),
            severity="error",
            fix_hint="Run: ./atoms vendor setup"
        ),
        
        # Requirements
        DeploymentCheck(
            name="📄 Requirements: Production file exists",
            check_fn=lambda: checker.check_file_exists("requirements-prod.txt", "requirements-prod.txt"),
            severity="error",
            fix_hint="Run: ./atoms vendor setup"
        ),
        DeploymentCheck(
            name="📄 Requirements: No editable installs",
            check_fn=lambda: checker.check_file_not_contains("requirements-prod.txt", r"^-e ", "no editable installs"),
            severity="error",
            fix_hint="Run: ./atoms vendor setup"
        ),
        
        # Sitecustomize
        DeploymentCheck(
            name="🐍 Python: sitecustomize.py exists",
            check_fn=lambda: checker.check_file_exists("sitecustomize.py", "sitecustomize.py"),
            severity="error",
            fix_hint="Run: ./atoms vendor setup"
        ),
        DeploymentCheck(
            name="🐍 Python: sitecustomize adds pheno_vendor",
            check_fn=lambda: checker.check_file_contains("sitecustomize.py", "pheno_vendor", "pheno_vendor reference"),
            severity="warning",
            fix_hint="Run: ./atoms vendor setup"
        ),
        
        # Vercel config
        DeploymentCheck(
            name="⚙️  Vercel: vercel.json exists",
            check_fn=lambda: checker.check_file_exists("vercel.json", "vercel.json"),
            severity="error",
        ),
        DeploymentCheck(
            name="⚙️  Vercel: buildCommand configured",
            check_fn=lambda: checker.check_file_contains("vercel.json", "buildCommand", "buildCommand"),
            severity="warning",
        ),
        
        # Build script
        DeploymentCheck(
            name="🔨 Build: build.sh exists",
            check_fn=lambda: checker.check_file_exists("build.sh", "build.sh"),
            severity="error",
        ),
        DeploymentCheck(
            name="🔨 Build: build.sh is executable",
            check_fn=lambda: checker.check_file_executable("build.sh", "build.sh"),
            severity="warning",
            fix_hint="Run: chmod +x build.sh"
        ),
        
        # Environment files
        DeploymentCheck(
            name="🔐 Environment: .env.preview exists",
            check_fn=lambda: checker.check_file_exists(".env.preview", ".env.preview"),
            severity="warning",
            fix_hint="Create .env.preview for preview deployments"
        ),
        DeploymentCheck(
            name="🔐 Environment: .env.production exists",
            check_fn=lambda: checker.check_file_exists(".env.production", ".env.production"),
            severity="warning",
            fix_hint="Create .env.production for production deployments"
        ),
        
        # Git tracking
        DeploymentCheck(
            name="📝 Git: pheno_vendor tracked",
            check_fn=lambda: checker.check_git_tracked("pheno_vendor", "pheno_vendor"),
            severity="error",
            fix_hint="Run: git add pheno_vendor/"
        ),
        DeploymentCheck(
            name="📝 Git: requirements-prod.txt tracked",
            check_fn=lambda: checker.check_git_tracked("requirements-prod.txt", "requirements-prod.txt"),
            severity="error",
            fix_hint="Run: git add requirements-prod.txt"
        ),
        DeploymentCheck(
            name="📝 Git: sitecustomize.py tracked",
            check_fn=lambda: checker.check_git_tracked("sitecustomize.py", "sitecustomize.py"),
            severity="error",
            fix_hint="Run: git add sitecustomize.py"
        ),
        DeploymentCheck(
            name="📝 Git: No uncommitted changes",
            check_fn=lambda: checker.check_no_uncommitted_changes(),
            severity="warning",
            fix_hint="Commit changes before deploying"
        ),
    ]


def main():
    """Run deployment checks."""
    checks = create_vercel_deployment_checks()
    checker = DeploymentChecker()
    errors, warnings = checker.run_all(checks)
    
    if errors == 0 and warnings == 0:
        print("🚀 Ready to deploy:")
        print("   ./atoms deploy --preview      # Deploy to preview")
        print("   ./atoms deploy --production   # Deploy to production")
        print()
        return 0
    elif errors == 0:
        print("You can deploy, but consider addressing warnings:")
        print("   ./atoms deploy --preview      # Deploy to preview")
        print()
        return 0
    else:
        print("Fix errors before deploying:")
        print("   ./atoms vendor setup          # Setup vendoring")
        print("   git add pheno_vendor/ requirements-prod.txt sitecustomize.py")
        print("   git commit -m 'Add vendored packages'")
        print()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

