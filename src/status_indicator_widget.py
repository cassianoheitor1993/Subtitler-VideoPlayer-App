"""
Status Indicator Widget
Displays progress of background tasks in the top-right corner
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor
from background_task_manager import TaskInfo, TaskStatus, TaskType


class TaskIndicator(QFrame):
    """Individual task indicator showing progress"""
    
    clicked = pyqtSignal(str)  # task_id
    cancel_requested = pyqtSignal(str)  # task_id
    
    def __init__(self, task_info: TaskInfo, parent=None):
        super().__init__(parent)
        self.task_info = task_info
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for task indicator"""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #3d3d3d;
                border: 1px solid #0e639c;
            }
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        # Header with icon and cancel button
        header_layout = QHBoxLayout()
        
        # Task icon and title
        if self.task_info.task_type == TaskType.AI_GENERATION:
            icon = "🤖"
            title = "AI Generation"
        elif self.task_info.task_type == TaskType.TRANSLATION:
            icon = "🌍"
            title = "Translation"
        elif self.task_info.task_type == TaskType.PROXY_TRANSCODE:
            icon = "🎬"
            title = "Proxy 1080p"
        else:
            icon = "⚙️"
            title = "Background Task"
        
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #ffffff; border: none;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(20, 20)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.task_info.task_id))
        self.cancel_btn.setToolTip("Cancel task")
        header_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self.task_info.progress)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                text-align: center;
                background-color: #1e1e1e;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status message
        self.message_label = QLabel(self.task_info.message)
        self.message_label.setFont(QFont("Arial", 8))
        self.message_label.setStyleSheet("color: #cccccc; border: none;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
    
    def update_progress(self, task_info: TaskInfo):
        """Update progress display"""
        self.task_info = task_info
        self.progress_bar.setValue(task_info.progress)
        self.message_label.setText(task_info.message)
        
        # Update style based on status
        if task_info.status == TaskStatus.COMPLETED:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #1e1e1e;
                    color: white;
                }
                QProgressBar::chunk {
                    background-color: #4caf50;
                    border-radius: 2px;
                }
            """)
            self.cancel_btn.hide()
        elif task_info.status == TaskStatus.FAILED:
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #3d3d3d;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #1e1e1e;
                    color: white;
                }
                QProgressBar::chunk {
                    background-color: #f44336;
                    border-radius: 2px;
                }
            """)
            self.cancel_btn.hide()
    
    def mousePressEvent(self, event):
        """Handle click to expand details"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.task_info.task_id)
        super().mousePressEvent(event)


class StatusIndicatorWidget(QWidget):
    """Widget that displays all background tasks"""
    
    task_clicked = pyqtSignal(str)  # task_id
    cancel_requested = pyqtSignal(str)  # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_indicators = {}  # task_id -> TaskIndicator
        self.setup_ui()
        
        # Auto-hide timer for completed tasks
        self.cleanup_timer = QTimer()
        self.cleanup_timer.setInterval(5000)  # 5 seconds
        self.cleanup_timer.timeout.connect(self.cleanup_completed_tasks)
        self.cleanup_timer.start()
    
    def setup_ui(self):
        """Setup the UI"""
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.setLayout(self.main_layout)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # Make widget float on top
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Initially hidden
        self.hide()
    
    def add_task(self, task_info: TaskInfo):
        """Add a new task indicator"""
        if task_info.task_id in self.task_indicators:
            return
        
        indicator = TaskIndicator(task_info, self)
        indicator.clicked.connect(self.task_clicked.emit)
        indicator.cancel_requested.connect(self.cancel_requested.emit)
        
        self.task_indicators[task_info.task_id] = indicator
        self.main_layout.addWidget(indicator)
        
        # Show widget
        self.show()
        
        # Animate entrance
        self.animate_indicator(indicator, show=True)
    
    def update_task(self, task_info: TaskInfo):
        """Update existing task indicator"""
        if task_info.task_id in self.task_indicators:
            indicator = self.task_indicators[task_info.task_id]
            indicator.update_progress(task_info)
    
    def remove_task(self, task_id: str):
        """Remove task indicator"""
        if task_id in self.task_indicators:
            indicator = self.task_indicators[task_id]
            self.animate_indicator(indicator, show=False)
            
            # Schedule deletion
            QTimer.singleShot(300, lambda: self._delete_indicator(task_id))
    
    def _delete_indicator(self, task_id: str):
        """Actually delete the indicator"""
        if task_id in self.task_indicators:
            indicator = self.task_indicators[task_id]
            self.main_layout.removeWidget(indicator)
            indicator.deleteLater()
            del self.task_indicators[task_id]
        
        # Hide widget if no more tasks
        if not self.task_indicators:
            self.hide()
    
    def cleanup_completed_tasks(self):
        """Auto-remove completed/failed tasks after delay"""
        to_remove = []
        for task_id, indicator in self.task_indicators.items():
            if indicator.task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            self.remove_task(task_id)
    
    def animate_indicator(self, indicator: TaskIndicator, show: bool):
        """Animate indicator appearance/disappearance"""
        animation = QPropertyAnimation(indicator, b"maximumHeight")
        animation.setDuration(200)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        if show:
            animation.setStartValue(0)
            animation.setEndValue(200)
        else:
            animation.setStartValue(indicator.height())
            animation.setEndValue(0)
        
        animation.start()
