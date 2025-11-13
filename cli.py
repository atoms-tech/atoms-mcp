"""Atoms MCP CLI - Command-line interface for Atoms MCP Server.

Usage:
    atoms run          - Start the MCP server
    atoms update       - Update dependencies (like npm update)
    atoms health       - Check server health
    atoms version      - Show version info
    atoms --help       - Show this help message

Update subcommands:
    atoms update               - Interactive update (prompts for what to update)
    atoms update --all         - Update all dependencies
    atoms update --deps        - Update production dependencies only
    atoms update --dev         - Update development dependencies only
    atoms update --check       - Check for updates without installing
    atoms update --outdated    - Show outdated packages
"""

import sys
import typer
from typing import Optional
import subprocess
import json

app = typer.Typer(
    name="atoms",
    help="Atoms MCP Server - FastMCP server for Atoms platform",
    pretty_exceptions_show_locals=False,
)


@app.command()
def run(
    host: str = typer.Option("0.0.0.0", help="Host to bind server to"),
    port: int = typer.Option(8000, help="Port to run server on"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """Start the Atoms MCP Server.
    
    Starts a FastMCP server that provides MCP tools for:
    - Entity management (organizations, projects, documents, requirements, tests)
    - Workspace navigation
    - Entity relationships
    - Queries and search
    - Workflow automation
    
    Example:
        atoms run --port 8001 --debug
    """
    from server import main
    
    # Set environment for server startup
    if debug:
        import os
        os.environ["DEBUG"] = "true"
    
    print(f"🚀 Starting Atoms MCP Server on {host}:{port}")
    if debug:
        print("🔧 Debug mode enabled")
    
    main()


@app.command()
def health() -> None:
    """Check if the server is running and healthy."""
    import subprocess
    import os
    
    try:
        # Try to connect to running server
        import httpx
        client = httpx.Client(timeout=5.0)
        response = client.get("http://localhost:8000/health", timeout=5.0)
        
        if response.status_code == 200:
            print("✅ Server is healthy")
            sys.exit(0)
        else:
            print(f"⚠️  Server returned: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    print("Atoms MCP Server v0.1.0")
    print("FastMCP-based consolidated MCP server")


@app.command()
def update(
    all: bool = typer.Option(False, "--all", help="Update all dependencies"),
    deps: bool = typer.Option(False, "--deps", help="Update only production dependencies"),
    dev: bool = typer.Option(False, "--dev", help="Update only development dependencies"),
    check: bool = typer.Option(False, "--check", help="Check for updates without installing"),
    outdated: bool = typer.Option(False, "--outdated", help="Show outdated packages"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate update without making changes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output with details"),
) -> None:
    """Update project dependencies (similar to npm update).
    
    This command manages Python package dependencies via uv (UV package manager).
    It provides rich visual output with progress bars, dependency trees, and reports.
    
    Examples:
        atoms update --all               # Update all dependencies
        atoms update --deps              # Update only production deps
        atoms update --dev               # Update only dev deps
        atoms update --all --dry-run     # Preview updates without applying
        atoms update --outdated          # Show outdated packages
        atoms update -v                  # Verbose output
    
    Uses UV package manager for fast, reliable updates.
    Updates are made to pyproject.toml and uv.lock files.
    """
    try:
        from cli_update import (
            print_header,
            print_ascii_diagram,
            print_dependency_summary,
            show_update_plan,
            show_package_matrix,
            show_update_strategy,
            show_error_state,
            execute_update_with_visualization,
            DependencyAnalyzer,
        )
    except ImportError:
        print("⚠️  Rich CLI not available. Install with: pip install rich")
        print("Falling back to basic update...")
        _run_update(all=all, deps=deps, dev=dev, dry_run=dry_run, interactive=False)
        return
    
    # Print header
    print_header()
    
    # Analyze dependencies
    analyzer = DependencyAnalyzer()
    if not analyzer.load_dependencies():
        show_error_state(
            "Failed to load pyproject.toml",
            "Ensure pyproject.toml exists in project root"
        )
        sys.exit(1)
    
    # Show dependency summary
    print_dependency_summary(analyzer)
    
    # Handle --outdated flag
    if outdated:
        print("\n🔍 Checking for outdated packages...")
        _show_outdated_packages()
        return
    
    # Handle --check flag
    if check:
        print("\n🔍 Checking for available updates (dry-run)...")
        all_deps = analyzer.get_all_deps() if hasattr(analyzer, 'get_all_deps') else (analyzer.prod_deps + analyzer.dev_deps)
        execute_update_with_visualization(all_deps, dry_run=True, verbose=verbose)
        return
    
    # Determine what to update
    update_deps = []
    if all or (not deps and not dev):
        update_deps = analyzer.prod_deps + analyzer.dev_deps
    elif deps:
        update_deps = analyzer.prod_deps
    elif dev:
        update_deps = analyzer.dev_deps
    
    if not update_deps:
        print("ℹ️  No dependencies to update")
        return
    
    # Show update plan
    show_update_plan(all or (not deps and not dev), deps, dev, dry_run)
    
    # Show package matrix
    show_package_matrix(analyzer.prod_deps, analyzer.dev_deps)
    
    # Execute with visualization
    success, duration = execute_update_with_visualization(
        update_deps,
        dry_run=dry_run,
        verbose=verbose
    )
    
    if not success:
        sys.exit(1)


def _show_package_info() -> None:
    """Display current package version and info."""
    try:
        result = subprocess.run(
            ["uv", "pip", "index", "--no-pep-517"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Try to read from pyproject.toml
        try:
            with open("pyproject.toml", "r") as f:
                for line in f:
                    if line.startswith("name ="):
                        print(f"  {line.strip()}")
                    elif line.startswith("version ="):
                        print(f"  {line.strip()}")
                        break
        except FileNotFoundError:
            print("  ℹ️  pyproject.toml not found")
        
        # Show lock file status
        try:
            with open("uv.lock", "r") as f:
                lines = len(f.readlines())
                print(f"  📌 uv.lock: {lines} lines")
        except FileNotFoundError:
            print("  ⚠️  uv.lock not found")
            
    except Exception as e:
        print(f"  ⚠️  Could not read package info: {e}")


def _show_outdated_packages() -> None:
    """Show outdated packages using uv."""
    try:
        # Use pip list to check for outdated packages
        result = subprocess.run(
            ["python", "-m", "pip", "list", "--outdated"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            if result.stdout:
                print("\n📦 Outdated Packages:")
                print(result.stdout)
            else:
                print("\n✅ All packages are up to date!")
        else:
            print(f"⚠️  Could not check outdated packages: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error checking outdated packages: {e}")


def _run_update(
    all: bool = False,
    deps: bool = False,
    dev: bool = False,
    dry_run: bool = False,
    interactive: bool = True
) -> None:
    """Run the actual update using uv."""
    try:
        cmd = ["uv", "pip", "install", "--upgrade"]
        
        # Add dry-run flag if needed
        if dry_run:
            print("  (dry-run mode - no changes will be made)\n")
            # Note: pip install doesn't have --dry-run, so we'll just show what would happen
            # by running with --no-deps and then showing the plan
        
        # Determine what to update
        if all or (not deps and not dev):
            # Update everything
            print("  🔄 Updating all dependencies from pyproject.toml...")
            
            # Get dependencies from pyproject.toml
            deps_list = _get_all_dependencies()
            
            if deps_list:
                if dry_run:
                    print(f"\n📦 Would install/upgrade {len(deps_list)} packages:")
                    for dep in sorted(deps_list)[:10]:  # Show first 10
                        print(f"     • {dep}")
                    if len(deps_list) > 10:
                        print(f"     ... and {len(deps_list) - 10} more")
                    print(f"\n✅ Dry-run complete. Use 'atoms update --all' to apply changes.")
                else:
                    cmd.extend(deps_list)
                    _execute_pip_command(cmd)
            else:
                print("  ℹ️  No dependencies found to update")
                
        elif deps:
            print("  🔄 Updating production dependencies only...")
            deps_list = _get_prod_dependencies()
            
            if deps_list:
                if dry_run:
                    print(f"\n📦 Would install/upgrade {len(deps_list)} packages:")
                    for dep in sorted(deps_list)[:10]:
                        print(f"     • {dep}")
                    if len(deps_list) > 10:
                        print(f"     ... and {len(deps_list) - 10} more")
                    print(f"\n✅ Dry-run complete. Use 'atoms update --deps' to apply changes.")
                else:
                    cmd.extend(deps_list)
                    _execute_pip_command(cmd)
            else:
                print("  ℹ️  No production dependencies found to update")
                
        elif dev:
            print("  🔄 Updating development dependencies only...")
            deps_list = _get_dev_dependencies()
            
            if deps_list:
                if dry_run:
                    print(f"\n📦 Would install/upgrade {len(deps_list)} packages:")
                    for dep in sorted(deps_list)[:10]:
                        print(f"     • {dep}")
                    if len(deps_list) > 10:
                        print(f"     ... and {len(deps_list) - 10} more")
                    print(f"\n✅ Dry-run complete. Use 'atoms update --dev' to apply changes.")
                else:
                    cmd.extend(deps_list)
                    _execute_pip_command(cmd)
            else:
                print("  ℹ️  No development dependencies found to update")
        
        if not dry_run and not (deps or dev or all):
            print("✅ Update complete!")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")
        sys.exit(1)


def _get_all_dependencies() -> list:
    """Get all dependencies from pyproject.toml."""
    deps = set()
    deps.update(_get_prod_dependencies())
    deps.update(_get_dev_dependencies())
    return list(deps)


def _get_prod_dependencies() -> list:
    """Get production dependencies from pyproject.toml."""
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        # Simple parsing - find dependencies section
        if "dependencies = [" in content:
            start = content.find("dependencies = [")
            end = content.find("]", start)
            deps_str = content[start:end]
            
            # Extract package names
            deps = []
            for line in deps_str.split("\n"):
                line = line.strip().strip('"').strip("'").strip(",")
                if line and not line.startswith("#") and line != "dependencies = [":
                    # Extract package name (before ==, >=, etc.)
                    pkg = line.split(">")[0].split("<")[0].split("=")[0].split(";")[0].strip()
                    if pkg:
                        deps.append(pkg)
            return deps
        return []
    except Exception as e:
        print(f"  ⚠️  Could not read dependencies: {e}")
        return []


def _get_dev_dependencies() -> list:
    """Get development dependencies from pyproject.toml."""
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        # Simple parsing - find dev-dependencies section
        if "dev-dependencies" in content or "[tool.uv.dev-dependencies]" in content:
            if "[tool.uv.dev-dependencies]" in content:
                start = content.find("[tool.uv.dev-dependencies]")
                # Find next section or EOF
                next_section = content.find("[", start + 1)
                if next_section == -1:
                    end = len(content)
                else:
                    end = next_section
                deps_str = content[start:end]
            else:
                start = content.find("dev-dependencies = [")
                end = content.find("]", start)
                deps_str = content[start:end]
            
            # Extract package names
            deps = []
            for line in deps_str.split("\n"):
                line = line.strip().strip('"').strip("'").strip(",")
                if line and not line.startswith("#") and not line.startswith("["):
                    # Extract package name
                    pkg = line.split(">")[0].split("<")[0].split("=")[0].split(";")[0].strip()
                    if pkg and pkg != "dev-dependencies":
                        deps.append(pkg)
            return deps
        return []
    except Exception as e:
        print(f"  ⚠️  Could not read dev-dependencies: {e}")
        return []


def _execute_pip_command(cmd: list) -> None:
    """Execute a pip command and show results."""
    try:
        result = subprocess.run(
            cmd,
            timeout=300,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Update completed successfully!")
        else:
            print(f"\n⚠️  Update completed with some issues")
            sys.exit(result.returncode)
            
    except subprocess.TimeoutExpired:
        print("\n❌ Update timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error executing update: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
