#!/usr/bin/env python3
"""
Atoms MCP - Unified Entry Point

A consolidated CLI for all Atoms MCP operations using pheno-sdk libraries.

Commands:
    start       Start local MCP server with CloudFlare tunnel
    test        Run test suite with mcp-QA framework
    deploy      Deploy to local (KInfra tunnel), preview, or production
    validate    Validate configuration and setup
    verify      Verify system setup and dependencies
    vendor      Manage pheno-sdk vendoring (uses deploy-kit)
    config      Show or validate configuration
    schema      Manage database schema synchronization
    embeddings  Manage vector embeddings
    check       Check deployment readiness

Examples:
    atoms-mcp.py start                      # Start local server
    atoms-mcp.py start --port 50003         # Start on custom port
    atoms-mcp.py test --local --verbose     # Run tests locally
    atoms-mcp.py deploy --local             # Deploy locally via KInfra tunnel
    atoms-mcp.py deploy --preview           # Deploy to Vercel preview (devmcp.atoms.tech)
    atoms-mcp.py deploy --production        # Deploy to Vercel production (mcp.atoms.tech)
    atoms-mcp.py vendor setup               # Vendor pheno-sdk packages
    atoms-mcp.py validate                   # Validate configuration
    atoms-mcp.py verify                     # Verify setup
    atoms-mcp.py schema check               # Check schema drift
    atoms-mcp.py schema sync                # Sync schema from database
    atoms-mcp.py embeddings backfill        # Generate embeddings
    atoms-mcp.py embeddings status          # Check embedding status
"""

import argparse
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import pheno-sdk libraries with fallback
try:
    from observability import StructuredLogger, LogLevel
    logger = StructuredLogger(
        "atoms-mcp",
        service_name="atoms-mcp-cli",
        environment="local",
        level=LogLevel.INFO
    )
    USE_STRUCTURED_LOGGING = True
except ImportError:
    # Fallback to basic logging if observability-kit not available
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger("atoms-mcp")
    USE_STRUCTURED_LOGGING = False


def log_info(message, **kwargs):
    """Helper to log with or without structured logging."""
    if USE_STRUCTURED_LOGGING:
        logger.info(message, **kwargs)
    else:
        extra = ' '.join(f"{k}={v}" for k, v in kwargs.items())
        logger.info(f"{message} {extra}".strip())


def log_error(message, **kwargs):
    """Helper to log errors with or without structured logging."""
    if USE_STRUCTURED_LOGGING:
        logger.error(message, **kwargs)
    else:
        extra = ' '.join(f"{k}={v}" for k, v in kwargs.items())
        logger.error(f"{message} {extra}".strip())


def cmd_start(args):
    """Start local MCP server with CloudFlare tunnel."""
    log_info("Starting local MCP server", port=args.port, tunnel=not args.no_tunnel)

    # Use the Atoms-specific server manager
    try:
        from lib.atoms import start_atoms_server
        return start_atoms_server(
            port=args.port,
            verbose=args.verbose,
            no_tunnel=args.no_tunnel,
            logger=logger if USE_STRUCTURED_LOGGING else None
        )
    except ImportError as e:
        log_error(f"Could not import Atoms server library: {e}")
        print(f"\nError: Could not import Atoms server library: {e}")
        print("Make sure you're in the atoms_mcp-old directory.")
        return 1


def cmd_test(args):
    """Run test suite using mcp-QA framework."""
    log_info("Running test suite", local=args.local, verbose=args.verbose)
    
    # Import test runner
    try:
        from tests.test_main import main as test_main
    except ImportError as e:
        log_error(f"Could not import test_main: {e}")
        print(f"\nError: Could not import test_main: {e}")
        return 1
    
    # Convert args to sys.argv format for test_main
    sys.argv = ["test_main.py"]
    if args.local:
        sys.argv.append("--local")
    if args.verbose:
        sys.argv.append("--verbose")
    if args.categories:
        sys.argv.extend(["--categories"] + args.categories)
    if args.workers:
        sys.argv.extend(["--workers", str(args.workers)])
    if args.no_oauth:
        sys.argv.append("--no-oauth")
    if args.headless:
        sys.argv.append("--headless")
    
    return test_main()


def cmd_deploy(args):
    """Deploy to local (KInfra tunnel), preview, or production."""
    # Map environment
    if args.local:
        environment = "local"
    elif args.production:
        environment = "production"
    elif args.preview:
        environment = "preview"
    else:
        log_error("Must specify --local, --preview, or --production")
        print("Error: Must specify --local, --preview, or --production")
        return 1

    log_info("Deploying", environment=environment)

    # Handle local deployment (via KInfra tunnel)
    if environment == "local":
        print("\n" + "="*70)
        print("  Local Deployment via KInfra Tunnel")
        print("="*70)
        print("\nStarting local server with CloudFlare tunnel...")
        print("This provides HTTPS access at atomcp.kooshapari.com")
        print("Port is automatically managed by KInfra\n")

        # Use the start command with tunnel enabled (port managed by KInfra)
        args.port = None  # KInfra manages port allocation
        args.verbose = getattr(args, 'verbose', False)
        args.no_tunnel = False  # Force tunnel enabled for local deployment
        return cmd_start(args)

    # Handle Vercel deployments (preview/production)
    try:
        from lib.atoms import deploy_atoms_to_vercel
    except ImportError as e:
        log_error(f"Could not import Atoms deployment library: {e}")
        print(f"\nError: Could not import Atoms deployment library: {e}")
        return 1

    # Confirm production deployment
    if environment == "production":
        print("\n" + "!"*70)
        print("  WARNING: PRODUCTION DEPLOYMENT")
        print("!"*70)
        print("\nYou are about to deploy to PRODUCTION (atomcp.kooshapari.com)")
        print("This will affect all users immediately.")

        response = input("\nType 'yes' to continue: ")
        if response.lower() != 'yes':
            print("\nProduction deployment cancelled.")
            return 0

    return deploy_atoms_to_vercel(
        environment=environment,
        logger=logger if USE_STRUCTURED_LOGGING else None
    )


def cmd_validate(args):
    """Validate configuration using config-kit."""
    log_info("Validating configuration")

    try:
        # Import from archived entry point
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "archive" / "old_entry_points"))
        from test_config import main as validate_config
        return validate_config()
    except ImportError as e:
        log_error(f"Failed to import test_config: {e}")
        print(f"Error: Could not load configuration validator: {e}")
        print("Note: test_config.py was moved to archive/old_entry_points/")
        return 1


def cmd_verify(args):
    """Verify system setup and dependencies."""
    log_info("Verifying system setup")

    try:
        # Import from archived entry point
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "archive" / "old_entry_points"))
        from verify_setup import main as verify_setup
        return verify_setup()
    except ImportError as e:
        log_error(f"Failed to import verify_setup: {e}")
        print(f"Error: Could not load setup verifier: {e}")
        print("Note: verify_setup.py was moved to archive/old_entry_points/")
        return 1


def cmd_vendor(args):
    """Manage pheno-sdk vendoring using vendor_manager library."""
    log_info("Vendor management", action=args.vendor_action)

    try:
        from lib.vendor_manager import VendorManager

        vendor_mgr = VendorManager()

        if args.vendor_action == "setup":
            # Vendor all packages
            clean = getattr(args, 'clean', False)
            success = vendor_mgr.vendor_all(clean=clean)
            return 0 if success else 1

        elif args.vendor_action == "verify":
            # Verify vendored packages
            if not vendor_mgr.check_prerequisites():
                return 1

            success_count, error_count = vendor_mgr.verify_vendored_packages()

            if error_count == 0:
                print(f"\n✅ All vendored packages verified ({success_count} packages)")
                return 0
            else:
                print(f"\n⚠️  Verification complete with {error_count} errors")
                return 1

        elif args.vendor_action == "clean":
            # Clean vendor directory
            vendor_mgr.clean_vendor()
            return 0

        else:
            log_error(f"Unknown vendor action: {args.vendor_action}")
            return 1

    except Exception as e:
        log_error(f"Vendor error: {e}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_config(args):
    """Show or validate configuration using config-kit."""
    log_info("Configuration management", action=args.config_action)

    try:
        from pathlib import Path

        if args.config_action == "show":
            # Load and display configuration
            env_file = Path(__file__).parent / ".env"
            if env_file.exists():
                print(f"\nConfiguration from {env_file}:")
                print("-" * 70)
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Mask sensitive values
                            if "=" in line:
                                key, value = line.split("=", 1)
                                if any(s in key.upper() for s in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
                                    value = "***MASKED***"
                                print(f"{key}={value}")
                print("-" * 70)
            else:
                print(f"\nNo .env file found at {env_file}")
                return 1

        elif args.config_action == "validate":
            # Validate configuration
            return cmd_validate(args)

        return 0

    except Exception as e:
        log_error(f"Configuration error: {e}")
        print(f"Error: {e}")
        return 1


def cmd_schema(args):
    """Manage database schema synchronization."""
    log_info("Schema management", action=args.schema_action)

    try:
        from lib.schema_sync import SchemaSync

        sync = SchemaSync()

        if args.schema_action == "check":
            # Check for schema drift
            sync.db_schema = sync.get_supabase_schema()
            sync.local_schema = sync.get_local_schema()
            sync.differences = sync.compare_schemas()

            if not sync.differences:
                print(f"\n✅ No schema differences found")
                print(f"✅ Schemas are in sync\n")
                return 0
            else:
                sync.print_differences()
                print(f"\n⚠️  Schema drift detected!")
                print(f"Run with --regenerate to regenerate from database\n")
                return 1

        elif args.schema_action == "sync":
            # Regenerate schemas from database
            success = sync.regenerate_schemas()
            return 0 if success else 1

        elif args.schema_action == "diff":
            # Show detailed differences
            sync.db_schema = sync.get_supabase_schema()
            sync.local_schema = sync.get_local_schema()
            sync.differences = sync.compare_schemas()
            sync.print_differences()
            return 0

        elif args.schema_action == "report":
            # Generate report
            sync.db_schema = sync.get_supabase_schema()
            sync.local_schema = sync.get_local_schema()
            sync.differences = sync.compare_schemas()
            sync.generate_report()
            return 0

        else:
            log_error(f"Unknown schema action: {args.schema_action}")
            return 1

    except Exception as e:
        log_error(f"Schema error: {e}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_embeddings(args):
    """Manage vector embeddings."""
    log_info("Embeddings management", action=args.embeddings_action)

    import subprocess

    if args.embeddings_action == "backfill":
        script_path = Path(__file__).parent / "scripts" / "backfill_embeddings.py"
    elif args.embeddings_action == "status":
        script_path = Path(__file__).parent / "scripts" / "check_embedding_status.py"
    else:
        log_error(f"Unknown embeddings action: {args.embeddings_action}")
        return 1

    if not script_path.exists():
        log_error(f"Embeddings script not found: {script_path}")
        print(f"Error: {script_path} not found")
        return 1

    cmd = [sys.executable, str(script_path)]

    # Add any additional arguments
    if hasattr(args, 'batch_size') and args.batch_size:
        cmd.extend(["--batch-size", str(args.batch_size)])
    if hasattr(args, 'verbose') and args.verbose:
        cmd.append("--verbose")

    log_info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def cmd_check(args):
    """Check deployment readiness."""
    log_info("Checking deployment readiness")

    try:
        from lib.deployment_checker import create_vercel_deployment_checks, DeploymentChecker

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

    except Exception as e:
        log_error(f"Check error: {e}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point with subcommand routing."""
    parser = argparse.ArgumentParser(
        description="Atoms MCP - Unified CLI for all operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--version", action="version", version="atoms-mcp 1.0.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # START command
    start_parser = subparsers.add_parser("start", help="Start local MCP server")
    start_parser.add_argument("--port", type=int, help="Port to run on (default: 50002)")
    start_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    start_parser.add_argument("--no-tunnel", action="store_true", help="Disable CloudFlare tunnel")
    start_parser.set_defaults(func=cmd_start)
    
    # TEST command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument("--local", action="store_true", help="Use local server")
    test_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("--categories", nargs="+", help="Test categories to run")
    test_parser.add_argument("--workers", type=int, help="Number of parallel workers")
    test_parser.add_argument("--no-oauth", action="store_true", help="Skip OAuth tests")
    test_parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    test_parser.set_defaults(func=cmd_test)
    
    # DEPLOY command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy to local, preview, or production")
    deploy_group = deploy_parser.add_mutually_exclusive_group(required=True)
    deploy_group.add_argument("--local", action="store_true", help="Deploy locally via KInfra tunnel (atomcp.kooshapari.com)")
    deploy_group.add_argument("--preview", action="store_true", help="Deploy to Vercel preview (devmcp.atoms.tech)")
    deploy_group.add_argument("--production", action="store_true", help="Deploy to Vercel production (mcp.atoms.tech)")
    deploy_parser.add_argument("--verbose", action="store_true", help="Verbose logging for local deployment")
    deploy_parser.set_defaults(func=cmd_deploy, environment=None)
    
    # VALIDATE command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.set_defaults(func=cmd_validate)
    
    # VERIFY command
    verify_parser = subparsers.add_parser("verify", help="Verify system setup")
    verify_parser.set_defaults(func=cmd_verify)
    
    # VENDOR command
    vendor_parser = subparsers.add_parser("vendor", help="Manage pheno-sdk vendoring")
    vendor_parser.add_argument("vendor_action", choices=["setup", "verify", "clean"],
                              help="Vendor action: setup=vendor packages, verify=check vendored packages, clean=remove vendor dir")
    vendor_parser.add_argument("--clean", action="store_true", help="Clean vendor directory before setup (setup only)")
    vendor_parser.set_defaults(func=cmd_vendor)
    
    # CONFIG command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_parser.add_argument("config_action", choices=["show", "validate"], help="Config action")
    config_parser.set_defaults(func=cmd_config)

    # SCHEMA command
    schema_parser = subparsers.add_parser("schema", help="Database schema synchronization")
    schema_parser.add_argument("schema_action", choices=["check", "sync", "diff", "report"],
                              help="Schema action: check=check drift, sync=regenerate from DB, diff=show differences, report=generate report")
    schema_parser.set_defaults(func=cmd_schema)

    # EMBEDDINGS command
    embeddings_parser = subparsers.add_parser("embeddings", help="Vector embeddings management")
    embeddings_parser.add_argument("embeddings_action", choices=["backfill", "status"],
                                  help="Embeddings action: backfill=generate embeddings, status=check status")
    embeddings_parser.add_argument("--batch-size", type=int, help="Batch size for backfill")
    embeddings_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    embeddings_parser.set_defaults(func=cmd_embeddings)

    # CHECK command
    check_parser = subparsers.add_parser("check", help="Check deployment readiness")
    check_parser.set_defaults(func=cmd_check)

    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    try:
        return args.func(args)
    except Exception as e:
        log_error(f"Command failed: {e}")
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

