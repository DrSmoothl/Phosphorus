#!/usr/bin/env python3
"""Phosphorus development server runner."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the development server."""
    project_root = Path(__file__).parent

    # Change to project directory
    import os
    os.chdir(project_root)

    # Run with uv
    cmd = [sys.executable, "-m", "src.main"]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Server failed with exit code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
