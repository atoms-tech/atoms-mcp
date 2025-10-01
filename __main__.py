import sys
import os
import subprocess

from .server import main

if __name__ == "__main__":
    # Check for --local flag
    if "--local" in sys.argv:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        start_script = os.path.join(script_dir, "start_local.sh")

        # Execute the start_local.sh script
        try:
            subprocess.run([start_script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error starting local services: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: start_local.sh not found at {start_script}")
            sys.exit(1)
    else:
        main()

