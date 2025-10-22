#!/usr/bin/env python3
"""Legacy entry point retained for compatibility; delegates to `server.main`."""

from server import create_consolidated_server, main

# Create server instance for fastmcp run command
mcp = create_consolidated_server()

if __name__ == "__main__":
    main()
