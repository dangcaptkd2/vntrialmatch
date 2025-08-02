#!/usr/bin/env python3
"""
Main entry point for the trial matching system.

This script runs the Streamlit application from the new structure.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import streamlit.web.cli as stcli

    # Run the Streamlit app
    sys.argv = ["streamlit", "run", "src/app/app.py", "--server.port=8501"]
    sys.exit(stcli.main())
