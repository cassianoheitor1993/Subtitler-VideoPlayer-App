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

# Import and run
from subtitleplayer.video_player import main

if __name__ == "__main__":
    main()
