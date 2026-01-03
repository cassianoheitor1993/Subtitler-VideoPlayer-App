#!/usr/bin/env python3
"""
SubtitlePlayer - Professional Video Player with Native Subtitle Download
Main entry point
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from subtitleplayer.video_player import VideoPlayer


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("SubtitlePlayer")
    app.setOrganizationName("SubtitlePlayer")
    
    player = VideoPlayer()
    player.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
