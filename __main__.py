try:
    # Try relative import first (when running as module)
    from .server_oauth import main
except ImportError:
    # Fall back to absolute import (when running directly)
    from server_oauth import main

if __name__ == "__main__":
    main()

