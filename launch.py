#!/usr/bin/env python3
"""
Quick Launcher for SubtitlePlayer
Run this file directly from VS Code or terminal
"""

import sys
import os
from pathlib import Path

# Get the directory containing this script
script_dir = Path(__file__).parent.absolute()

# Add src to path
sys.path.insert(0, str(script_dir / "src"))

# Change to project directory
os.chdir(script_dir)

# Import and run
from video_player import main

if __name__ == "__main__":
    main()
