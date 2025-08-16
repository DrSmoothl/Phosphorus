#!/usr/bin/env python3
"""Phosphorus server entry point."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main application
if __name__ == "__main__":
    from src.main import main

    main()
