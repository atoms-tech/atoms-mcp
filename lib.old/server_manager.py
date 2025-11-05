#!/usr/bin/env python3
"""
Server management for atoms CLI
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path


async def handle_server_command(args):
    """Handle server commands"""
    if args.server_command == "start":
        await start_server(args)
    elif args.server_command == "stop":
        await stop_server(args)
    elif args.server_command == "status":
        await check_status(args)
    else:
        print(f"Unknown server command: {args.server_command}")
        sys.exit(1)


async def start_server(args):
    """Start atoms server"""
    print(f"🚀 Starting atoms server on {args.host}:{args.port}")

    # Build command
    cmd = [
        "fastmcp",
        "run",
        "fastmcp.json",
        "--skip-source" if args.skip_source else "",
        "--transport",
        "stdio",
        "--log-level",
        "INFO",
    ]

    # Remove empty strings
    cmd = [c for c in cmd if c]

    # Set environment
    env = os.environ.copy()
    env["ATOMS_PORT"] = str(args.port)

    try:
        if args.foreground:
            # Run in foreground
            process = await asyncio.create_subprocess_exec(*cmd, env=env, cwd=Path.cwd())

            print(f"✅ Server started on {args.host}:{args.port}")
            print("Press Ctrl+C to stop")

            # Wait for process
            await process.communicate()
        else:
            # Run in background
            # Use asyncio.to_thread for file I/O to avoid blocking
            log_path = Path("atoms-server.log")

            def append_to_log():
                with log_path.open("a") as f:
                    f.write(f"Starting server on {args.host}:{args.port}\n")

            await asyncio.to_thread(append_to_log)

            # Open log files before Popen (sync operation outside async context)
            def open_log_file(mode):
                return log_path.open(mode)

            log_file_out = await asyncio.to_thread(open_log_file, "a")
            log_file_err = await asyncio.to_thread(open_log_file, "a")

            process = subprocess.Popen(cmd, env=env, cwd=Path.cwd(), stdout=log_file_out, stderr=log_file_err)

            print(f"✅ Server started in background on {args.host}:{args.port}")
            print("📝 Logs: atoms-server.log")

            # Save PID
            pid_path = Path("atoms-server.pid")
            await asyncio.to_thread(pid_path.write_text, str(process.pid))

            print(f"🔢 PID: {process.pid}")

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


async def stop_server(args):
    """Stop atoms server"""
    pid_path = Path("atoms-server.pid")
    try:
        # Read PID
        pid = int(await asyncio.to_thread(pid_path.read_text))

        # Kill process
        if args.force:
            os.kill(pid, 9)  # SIGKILL
        else:
            os.kill(pid, 15)  # SIGTERM

        print(f"✅ Server stopped (PID: {pid})")

        # Remove PID file
        pid_path.unlink()

    except FileNotFoundError:
        print("⚠️ Server PID file not found. Server may not be running.")
    except ProcessLookupError:
        print("⚠️ Server process not found. Server may have already stopped.")
        if pid_path.exists():
            pid_path.unlink()
    except Exception as e:
        print(f"❌ Error stopping server: {e}")
        sys.exit(1)


async def check_status(args):
    """Check server status"""
    pid_path = Path("atoms-server.pid")
    try:
        # Read PID
        pid = int(await asyncio.to_thread(pid_path.read_text))

        # Check if process exists
        try:
            os.kill(pid, 0)  # Just checking if process exists
            print(f"✅ Server is running (PID: {pid})")

            # Try to get process info
            try:
                import psutil

                p = psutil.Process(pid)
                print(f"🕒 Running since: {p.create_time()}")
                print(f"💾 Memory: {p.memory_info().rss // (1024 * 1024)} MB")
            except ImportError:
                print("📊 Install psutil for detailed stats: pip install psutil")

        except ProcessLookupError:
            print("⚠️ Server PID file exists but process not found. Server may have crashed.")
            if pid_path.exists():
                pid_path.unlink()

    except FileNotFoundError:
        print("⚠️ Server is not running.")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        sys.exit(1)
