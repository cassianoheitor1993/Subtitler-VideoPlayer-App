# Developer Quick Reference

**SubtitlePlayer Development Cheat Sheet**

## Quick Start

```bash
# Activate environment
source /home/cmedeiros/Documents/Cassiano-Portfolio/.venv/bin/activate

# Run app
cd /home/cmedeiros/Documents/Cassiano-Portfolio/Subtitler-App/SubtitlePlayer
python launch.py

# Run with debugger: Press F5 in VS Code
```

## Project Structure

```
src/
├── video_player.py              # Main app (812 lines)
├── subtitle_settings_dialog.py  # Settings UI (responsive grid)
├── subtitle_search_dialog.py    # OpenSubtitles search
├── ai_subtitle_dialog.py        # AI generation UI
├── subtitle_overlay.py          # Subtitle rendering
├── subtitle_parser.py           # SRT/VTT/ASS parser
├── subtitle_translator.py       # Translation backend
├── ai_subtitle_generator.py     # Whisper integration
├── config_manager.py            # JSON config
└── opensubtitles_api.py         # API client
```

## Common Imports

```python
# PyQt6
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QPushButton,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont

# Standard
import os, sys, logging
from typing import List, Dict, Optional

# VLC
import vlc

# Project
from config_manager import ConfigManager, SubtitleStyle
from subtitle_parser import SubtitleParser, SubtitleEntry
```

## Code Templates

### Dialog Template
```python
class NewDialog(QDialog):
    completed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.resize(800, 600)
        self.init_ui()
        self.apply_style()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Add widgets...
    
    def apply_style(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #cccccc; }
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
```

### Worker Thread Template
```python
class WorkerThread(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, data):
        super().__init__()
        self.data = data
    
    def run(self):
        try:
            for i, item in enumerate(self.data):
                self.progress.emit(f"Processing {i}", i*100//len(self.data))
                # Work...
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### Error Handling Pattern
```python
try:
    result = operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    QMessageBox.warning(self, "Error", f"File not found: {e}")
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    QMessageBox.critical(self, "Error", str(e))
```

## VLC Setup

```python
import vlc
import os

# Quiet mode
os.environ['VLC_VERBOSE'] = '-1'
instance = vlc.Instance('--quiet', '--no-xlib')
player = instance.media_player_new()

# Get time in seconds
time_ms = player.get_time()
time_sec = time_ms / 1000.0

# Cleanup
def closeEvent(self, event):
    if self.media_player:
        self.media_player.stop()
    super().closeEvent(event)
```

## PyQt6 Patterns

### Responsive Grid Layout
```python
# Create grid
layout = QGridLayout()

# Add widgets
layout.addWidget(widget1, 0, 0)  # row 0, col 0
layout.addWidget(widget2, 0, 1)  # row 0, col 1

# Rearrange on resize
def resizeEvent(self, event):
    width = self.width()
    if width > 1200:
        # 3 columns
    elif width > 900:
        # 2 columns
    else:
        # 1 column
```

### Signal/Slot Connection
```python
# With lambda for parameters
button.clicked.connect(lambda: self.handle(param))

# Direct
button.clicked.connect(self.handle)

# Disconnect
button.clicked.disconnect()
```

## File Operations

```python
# Always absolute paths
path = os.path.abspath(path)

# Check existence
if not os.path.exists(path):
    raise FileNotFoundError(f"Not found: {path}")

# Pathlib for modern handling
from pathlib import Path
subtitle = Path(video_file).with_suffix('.srt')
```

## User Feedback

```python
# Status updates with emoji
self.status_label.setText("🔄 Processing...")
self.status_label.setText("✓ Complete")
self.status_label.setText("❌ Error")

# Progress
for i, item in enumerate(items):
    pct = int((i / len(items)) * 100)
    self.status.setText(f"Processing {i}/{len(items)} ({pct}%)")
    QApplication.processEvents()  # Keep responsive
```

## Keyboard Shortcuts

```python
def keyPressEvent(self, event):
    key = event.key()
    if key == Qt.Key.Key_Escape:
        self.exit_fullscreen()
    elif key == Qt.Key.Key_F or key == Qt.Key.Key_F11:
        self.toggle_fullscreen()
    elif key == Qt.Key.Key_Space:
        self.toggle_play_pause()
    else:
        super().keyPressEvent(event)
```

## Configuration

```python
# Save settings
config = ConfigManager()
config.save_subtitle_style(video_path, style)

# Load settings
style = config.load_subtitle_style(video_path)
if style is None:
    style = SubtitleStyle()  # Defaults
```

## Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

## Git Commands

```bash
# Check status
git status

# Stage and commit
git add -A
git commit -m "feat: Add feature description"

# Push to GitHub
git push origin main

# Create branch
git checkout -b feature/new-feature

# Merge branch
git checkout main
git merge feature/new-feature
```

## Commit Message Format

```
<type>: <summary>

<description>

Changes:
- Change 1
- Change 2

Closes #XX
```

**Types:** feat, fix, refactor, docs, style, test, chore

## Testing Checklist

- [ ] Load video (mp4, mkv, avi, mov, flv, wmv, webm)
- [ ] Play/pause, seek, volume
- [ ] Fullscreen (ESC, F, double-click, menu)
- [ ] Load subtitles (srt, vtt, ass)
- [ ] Subtitle styling
- [ ] Timing offset with preview
- [ ] Translation (if installed)
- [ ] AI generation (if installed)
- [ ] Responsive layout (resize window)
- [ ] No crashes or errors

## Common Issues

**"Qt platform plugin error"**
```bash
sudo apt install python3-pyqt6 libqt6gui6
```

**"VLC library not found"**
```bash
sudo apt install vlc libvlc-dev
pip install python-vlc==3.0.21203
```

**"Import errors in IDE"**
- Check Python interpreter in VS Code settings
- Restart IDE after changing interpreter

**"Debugger not working"**
- Use launch.py (not shell scripts)
- Check .vscode/launch.json
- Verify interpreter path

## Useful Commands

```bash
# Find files
find . -name "*.py" -type f

# Search in code
grep -r "function_name" src/

# Count lines
wc -l src/*.py

# Python syntax check
python -m py_compile src/video_player.py

# Run specific file
python src/video_player.py
```

## Performance Tips

- Cache expensive operations
- Use batch processing
- Keep UI responsive (processEvents)
- Cleanup in closeEvent()
- Use QThread for long operations

## Security Notes

- Never hardcode API keys
- Validate file paths
- Use subprocess with list (not shell=True)
- Sanitize user input

## Resources

- [PyQt6 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [VLC Python](https://www.olivieraubert.net/vlc/python-ctypes/)
- [PEP 8](https://pep8.org/)
- [.cursorrules](./.cursorrules) - Full AI instructions

## Critical Warnings

⚠️ **Fullscreen**: Always provide ESC handler
⚠️ **VLC**: Use --quiet flag
⚠️ **Threads**: Use QThread, not threading
⚠️ **Paths**: Always absolute paths
⚠️ **Errors**: User-friendly messages

---

**Need help?** Check `.cursorrules` for comprehensive guidelines.
