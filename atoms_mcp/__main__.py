"""Entry point for atoms_mcp command-line interface."""

import sys
from pathlib import Path

# Add parent directory to path so we can import root-level modules
parent = Path(__file__).parent.parent
sys.path.insert(0, str(parent))

from cli import main

if __name__ == "__main__":
    main()
