# GitHub Copilot Instructions for SubtitlePlayer

## Project Context
This is SubtitlePlayer - a professional Linux video player with subtitle management, built with Python 3.8+, PyQt6, and VLC backend.

## Code Generation Guidelines

### Always Include

1. **Type Hints**
```python
def parse_subtitle(file_path: str) -> List[SubtitleEntry]:
    pass
```

2. **Docstrings**
```python
"""
Brief description.

Args:
    param: Description

Returns:
    Description

Raises:
    ExceptionType: When it happens
"""
```

3. **Error Handling**
```python
try:
    result = operation()
except SpecificError as e:
    logger.error(f"Context: {e}")
    # User feedback
```

4. **Logging**
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Status message")
```

### PyQt6 Patterns

**Signals and Slots:**
```python
# Define signals
class MyWidget(QWidget):
    data_changed = pyqtSignal(object)
    
    # Connect with lambda for params
    button.clicked.connect(lambda: self.handle(param))
```

**Responsive Layouts:**
```python
# Use QGridLayout for multi-column
layout = QGridLayout()
layout.addWidget(widget, row, col)
```

**Dark Theme Styling:**
```python
self.setStyleSheet("""
    QWidget {
        background-color: #1e1e1e;
        color: #cccccc;
    }
    QPushButton {
        background-color: #0e639c;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
    }
""")
```

### VLC Integration

**Safe Instance Creation:**
```python
import vlc
import os

os.environ['VLC_VERBOSE'] = '-1'
instance = vlc.Instance('--quiet', '--no-xlib')
player = instance.media_player_new()
```

**Always Include Cleanup:**
```python
def closeEvent(self, event):
    if self.media_player:
        self.media_player.stop()
    super().closeEvent(event)
```

### File Operations

**Always Use Absolute Paths:**
```python
file_path = os.path.abspath(file_path)
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")
```

### User Feedback

**Progress Indicators:**
```python
self.status_label.setText(f"🔄 Processing {i}/{total}...")
# On complete:
self.status_label.setText(f"✓ Completed")
# On error:
self.status_label.setText(f"❌ Error: {error}")
```

**Modal Dialogs:**
```python
from PyQt6.QtWidgets import QMessageBox

QMessageBox.information(self, "Title", "Message")
QMessageBox.warning(self, "Warning", "Issue")
QMessageBox.critical(self, "Error", "Problem")
```

## Naming Conventions

- **Classes**: `SubtitleSettingsDialog`, `AISubtitleGenerator`
- **Methods**: `load_subtitle_file()`, `update_timing_preview()`
- **Variables**: `current_subtitles`, `media_player`, `font_size`
- **Constants**: `MAX_SUBTITLE_LENGTH`, `DEFAULT_FONT_SIZE`
- **Private**: `_internal_method()`, `_cache`
- **Signals**: `subtitles_changed`, `playback_started`

## Common Imports

```python
# PyQt6
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont

# Standard library
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# VLC
import vlc

# Project modules
from config_manager import ConfigManager, SubtitleStyle
from subtitle_parser import SubtitleParser, SubtitleEntry
```

## Testing Patterns

```python
# Manual test function
def test_feature():
    """Test feature with sample data"""
    app = QApplication(sys.argv)
    dialog = FeatureDialog()
    dialog.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    test_feature()
```

## Key Classes Structure

### Dialog Template
```python
class NewDialog(QDialog):
    # Signals
    completed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.init_ui()
        self.apply_style()
    
    def init_ui(self):
        """Setup UI"""
        pass
    
    def apply_style(self):
        """Apply dark theme"""
        pass
    
    def accept(self):
        """Handle OK button"""
        super().accept()
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
            result = self.process()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def process(self):
        # Long operation
        pass
```

## Security Considerations

- Never hardcode API keys (use env vars)
- Validate file paths (prevent traversal)
- Use subprocess with list (not shell=True)
- Sanitize user input before file operations

## Performance Tips

- Cache expensive operations
- Use batch processing where possible
- Keep UI responsive (processEvents in loops)
- Cleanup resources in closeEvent()

## Critical Warnings

⚠️ **Fullscreen**: Always provide ESC key handler and multiple exit methods
⚠️ **VLC**: Configure with --quiet to avoid console spam
⚠️ **Threads**: Use QThread, not threading module
⚠️ **Paths**: Always use absolute paths for files
⚠️ **Errors**: Show user-friendly messages, log technical details

## When Suggesting Code

1. Match existing code style
2. Include error handling
3. Add type hints and docstrings
4. Consider edge cases
5. Show complete, runnable examples
6. Explain complex logic with comments
7. Suggest tests where applicable

## Project-Specific Gotchas

- VLC time is in milliseconds (divide by 1000 for seconds)
- Subtitle timing uses seconds (float)
- Config stored at `~/.subtitleplayer/`
- Virtual env at `/home/cmedeiros/Documents/Cassiano-Portfolio/.venv`
- Launch app via `launch.py` (not direct video_player.py)
- ESC key must work in fullscreen (critical!)
