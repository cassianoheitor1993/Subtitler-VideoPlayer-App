"""
Simple Progress Indicator for Minimized Tasks
Shows a small floating widget in the corner during AI generation
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont


class SimpleProgressIndicator(QFrame):
    """Simple progress indicator for background tasks"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"[INDICATOR] Creating SimpleProgressIndicator with parent: {parent}")
        self.setup_ui()
        print(f"[INDICATOR] Widget created. Size: {self.width()}x{self.height()}")
        
    def setup_ui(self):
        """Setup the UI"""
        # Make it a floating window
        self.setWindowFlags(
            Qt.WindowType.Tool |  # Tool window (stays on top)
            Qt.WindowType.FramelessWindowHint |  # No window frame
            Qt.WindowType.WindowStaysOnTopHint  # Always on top
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        # Simple solid background - no transparency issues
        self.setStyleSheet("""
            SimpleProgressIndicator {
                background-color: #2d2d2d;
                border: 2px solid #0e639c;
                border-radius: 8px;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAutoFillBackground(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(12, 10, 12, 10)
        self.setLayout(layout)
        
        # Title - no stylesheet, just font and color via palette
        title = QLabel("🤖 AI Generation", self)
        font_title = QFont("Sans", 11, QFont.Weight.Bold)
        title.setFont(font_title)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Use QPalette for color
        from PyQt6.QtGui import QPalette, QColor
        palette_title = title.palette()
        palette_title.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))
        title.setPalette(palette_title)
        layout.addWidget(title)
        
        # Progress percentage label - bright and large
        self.progress_label = QLabel("0%", self)
        font_progress = QFont("Sans", 20, QFont.Weight.Bold)
        self.progress_label.setFont(font_progress)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        palette_progress = self.progress_label.palette()
        palette_progress.setColor(QPalette.ColorRole.WindowText, QColor("#4CAF50"))
        self.progress_label.setPalette(palette_progress)
        layout.addWidget(self.progress_label)
        
        # Status label (step info)
        self.status_label = QLabel("Starting...", self)
        font_status = QFont("Sans", 9)
        self.status_label.setFont(font_status)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        palette_status = self.status_label.palette()
        palette_status.setColor(QPalette.ColorRole.WindowText, QColor("#cccccc"))
        self.status_label.setPalette(palette_status)
        layout.addWidget(self.status_label)
        
        # Click to restore hint
        hint = QLabel("📌 Click to restore", self)
        font_hint = QFont("Sans", 8)
        hint.setFont(font_hint)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        palette_hint = hint.palette()
        palette_hint.setColor(QPalette.ColorRole.WindowText, QColor("#8cdaff"))
        hint.setPalette(palette_hint)
        layout.addWidget(hint)
        
        self.setFixedSize(180, 110)
        
    def mousePressEvent(self, event):
        """Handle click"""
        print(f"[INDICATOR] Mouse click detected!")
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        print(f"[INDICATOR] === SHOW EVENT ===")
        print(f"  - Visible: {self.isVisible()}")
        print(f"  - Size: {self.width()}x{self.height()}")
        print(f"  - Position: ({self.x()}, {self.y()})")
        print(f"  - Progress text: '{self.progress_label.text()}'")
        print(f"  - Status text: '{self.status_label.text()}'")
    
    def update_status(self, message: str):
        """Update status message - expects format like '45% - Processing step 23/50'"""
        print(f"[INDICATOR] update_status called: '{message}'")
        
        # Try to extract percentage and step info
        if '%' in message:
            parts = message.split('%', 1)
            try:
                percent = int(parts[0].strip())
                self.progress_label.setText(f"{percent}%")
                print(f"[INDICATOR] Set progress to {percent}%")
                
                # Update color based on progress using QPalette
                from PyQt6.QtGui import QPalette, QColor
                if percent < 33:
                    color = QColor("#FFA500")  # Orange
                elif percent < 66:
                    color = QColor("#FFD700")  # Gold
                else:
                    color = QColor("#4CAF50")  # Green
                
                palette = self.progress_label.palette()
                palette.setColor(QPalette.ColorRole.WindowText, color)
                self.progress_label.setPalette(palette)
                
                # Set step info
                if len(parts) > 1:
                    step_info = parts[1].strip(' -')
                    self.status_label.setText(step_info)
                    print(f"[INDICATOR] Set step info: '{step_info}'")
            except Exception as e:
                print(f"[INDICATOR] Error parsing percentage: {e}")
                # Fallback - just show the message
                self.status_label.setText(message)
        else:
            # No percentage, just show as status
            self.status_label.setText(message)
            print(f"[INDICATOR] Set status (no %): '{message}'")
        
        # Force repaint
        self.progress_label.update()
        self.status_label.update()
        self.update()
        self.repaint()
        print(f"[INDICATOR] Widget repainted")
    
    def start_animation(self):
        """Start animation (kept for compatibility, but not used)"""
        pass
    
    def stop_animation(self):
        """Stop animation (kept for compatibility, but not used)"""
        pass
