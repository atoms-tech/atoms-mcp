#!/usr/bin/env python3
"""
KINFRA Monitor CLI

Provides monitoring capabilities for KINFRA-managed services with live health checks,
log dumps, and process monitoring.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from pheno.infra.cli_monitor import create_monitor, monitor_service
    from pheno.infra.port_registry import PortRegistry
    KINFRA_AVAILABLE = True
except ImportError:
    KINFRA_AVAILABLE = False
    print("❌ KINFRA not available. Make sure pheno-sdk is installed.")
    sys.exit(1)


def list_services():
    """List all registered KINFRA services."""
    try:
        registry = PortRegistry()
        services = registry.get_all_services()

        if not services:
            print("📋 No KINFRA services found")
            return

        print("📋 KINFRA Services:")
        print("-" * 60)
        for name, info in services.items():
            print(f"  {name}:")
            print(f"    Port: {info.assigned_port}")
            print(f"    PID: {info.pid}")
            print(f"    Last seen: {info.last_seen}")
            print()
    except Exception as e:
        print(f"❌ Failed to list services: {e}")


def show_status(service_name: str = None):
    """Show status of services."""
    try:
        monitor = create_monitor()

        if service_name:
            # Show specific service
            registry = PortRegistry()
            service_info = registry.get_service(service_name)
            if not service_info:
                print(f"❌ Service '{service_name}' not found")
                return

            monitor.add_service(service_name, service_info.assigned_port)
        else:
            # Show all services
            registry = PortRegistry()
            services = registry.get_all_services()

            if not services:
                print("📋 No KINFRA services found")
                return

            for name, info in services.items():
                monitor.add_service(name, info.assigned_port)

        monitor.print_status()

    except Exception as e:
        print(f"❌ Failed to show status: {e}")


def show_logs(service_name: str, count: int = 20):
    """Show recent logs for a service."""
    try:
        registry = PortRegistry()
        service_info = registry.get_service(service_name)
        if not service_info:
            print(f"❌ Service '{service_name}' not found")
            return

        monitor = create_monitor()
        monitor.add_service(service_name, service_info.assigned_port)
        monitor.print_recent_logs(service_name, count)

    except Exception as e:
        print(f"❌ Failed to show logs: {e}")


def export_logs(service_name: str, file_path: str):
    """Export logs to a file."""
    try:
        registry = PortRegistry()
        service_info = registry.get_service(service_name)
        if not service_info:
            print(f"❌ Service '{service_name}' not found")
            return

        monitor = create_monitor()
        monitor.add_service(service_name, service_info.assigned_port)
        monitor.export_logs(service_name, file_path)

    except Exception as e:
        print(f"❌ Failed to export logs: {e}")


async def monitor_live(service_name: str = None):
    """Start live monitoring."""
    try:
        if service_name:
            # Monitor specific service
            registry = PortRegistry()
            service_info = registry.get_service(service_name)
            if not service_info:
                print(f"❌ Service '{service_name}' not found")
                return

            await monitor_service(service_name, service_info.assigned_port)
        else:
            # Monitor all services
            registry = PortRegistry()
            services = registry.get_all_services()

            if not services:
                print("📋 No KINFRA services found")
                return

            monitor = create_monitor()
            for name, info in services.items():
                monitor.add_service(name, info.assigned_port)

            await monitor.start_monitoring()

    except Exception as e:
        print(f"❌ Failed to start monitoring: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KINFRA Monitor - Monitor KINFRA-managed services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kinfra-monitor list                    # List all services
  kinfra-monitor status                  # Show status of all services
  kinfra-monitor status atoms-mcp-server # Show status of specific service
  kinfra-monitor logs atoms-mcp-server   # Show recent logs
  kinfra-monitor monitor                 # Start live monitoring
  kinfra-monitor export atoms-mcp-server logs.txt  # Export logs to file
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    subparsers.add_parser('list', help='List all KINFRA services')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show service status')
    status_parser.add_argument('service', nargs='?', help='Service name (optional)')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show recent logs')
    logs_parser.add_argument('service', help='Service name')
    logs_parser.add_argument('--count', '-c', type=int, default=20, help='Number of log entries to show')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export logs to file')
    export_parser.add_argument('service', help='Service name')
    export_parser.add_argument('file', help='Output file path')

    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start live monitoring')
    monitor_parser.add_argument('service', nargs='?', help='Service name (optional)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        list_services()
    elif args.command == 'status':
        show_status(args.service)
    elif args.command == 'logs':
        show_logs(args.service, args.count)
    elif args.command == 'export':
        export_logs(args.service, args.file)
    elif args.command == 'monitor':
        asyncio.run(monitor_live(args.service))


if __name__ == "__main__":
    main()
