#!/usr/bin/env python3
"""
Minimal server for atoms CLI
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

async def main():
    """Main server function"""
    print('🚀 Starting atoms server...')
    
    # Get arguments
    port = 8000
    host = 'localhost'
    foreground = True
    skip_source = False
    
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i+1])
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i+1]
        elif arg == '--foreground':
            foreground = True
        elif arg == '--skip-source':
            skip_source = True
    
    print(f'🎯 Running on {host}:{port}')
    
    # Build command
    cmd = [
        'fastmcp', 'run', 'fastmcp.json',
        '--skip-source' if skip_source else '',
        '--transport', 'stdio',
        '--log-level', 'INFO'
    ]
    
    # Remove empty strings
    cmd = [c for c in cmd if c]
    
    # Set environment
    env = os.environ.copy()
    env['ATOMS_PORT'] = str(port)
    
    try:
        if foreground:
            # Run in foreground
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                cwd=os.getcwd()
            )
            
            print(f'✅ Server started on {host}:{port}')
            print('Press Ctrl+C to stop')
            
            # Wait for process
            await process.communicate()
        else:
            # Run in background
            # Use asyncio.to_thread for file I/O to avoid blocking
            log_path = Path('atoms-server.log')

            def append_to_log():
                with log_path.open('a') as f:
                    f.write(f'Starting server on {host}:{port}\n')

            await asyncio.to_thread(append_to_log)

            # Open log files before Popen (sync operation outside async context)
            def open_log_file(mode):
                return log_path.open(mode)

            log_file_out = await asyncio.to_thread(open_log_file, 'a')
            log_file_err = await asyncio.to_thread(open_log_file, 'a')

            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=os.getcwd(),
                stdout=log_file_out,
                stderr=log_file_err
            )

            print(f'✅ Server started in background on {host}:{port}')
            print(f'📝 Logs: atoms-server.log')

            # Save PID
            pid_path = Path('atoms-server.pid')
            await asyncio.to_thread(pid_path.write_text, str(process.pid))

            print(f'🔢 PID: {process.pid}')
            
    except Exception as e:
        print(f'❌ Error starting server: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
