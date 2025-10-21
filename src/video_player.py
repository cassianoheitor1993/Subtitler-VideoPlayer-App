"""
Main Video Player Window
Professional video player with VLC backend and subtitle support
"""

import sys
import os
import socket
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QFileDialog, QFrame, QStyle, QApplication,
    QMenu, QMessageBox, QSplitter, QSplitterHandle, QSizePolicy,
    QDialog
)
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QPalette, QColor, QFont, QPainter, QPen
import vlc

# Suppress VLC warnings and debug messages
os.environ['VLC_VERBOSE'] = '-1'
import warnings
warnings.filterwarnings('ignore')

from subtitle_parser import SubtitleParser, SubtitleEntry
from config_manager import ConfigManager, SubtitleStyle
from ffmpeg_casting_manager import FFmpegCastingManager, FFmpegCastingError, FFmpegCastingConfig
from streaming_stats_dialog import StreamingStatsDialog
from background_task_manager import BackgroundTaskManager, TaskInfo, TaskStatus, TaskType
from stats_footer import StatsFooter
from debug_logger import debug_logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_VIDEO_PATH = PROJECT_ROOT / "temp" / "sample.mp4"
SAMPLE_CAST_URL_FILE = PROJECT_ROOT / "temp" / "start_cast_url.txt"
SAMPLE_CAST_LOG_FILE = PROJECT_ROOT / "temp" / "start_cast.log"


class SidebarSplitterHandle(QSplitterHandle):
    """Custom splitter handle with hand cursor and styled appearance"""

    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background-color: #1c1c1c;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1c1c1c"))
        handle_rect = self.rect()
        center_x = handle_rect.width() // 2
        top = handle_rect.height() // 2 - 12
        painter.setPen(QPen(QColor("#3a3a3a"), 2))
        for i in range(3):
            y = top + i * 8
            painter.drawLine(center_x - 6, y, center_x + 6, y)


class SidebarSplitter(QSplitter):
    """Splitter that uses custom handles"""

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setChildrenCollapsible(False)
        self.setHandleWidth(10)

    def createHandle(self):
        return SidebarSplitterHandle(self.orientation(), self)


class VideoFrame(QWidget):
    """Custom video frame widget with proper event handling"""
    
    double_clicked = pyqtSignal()
    resized = pyqtSignal()
    context_menu_requested = pyqtSignal(QPoint)
    mouse_moved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000;")
        self.setMouseTracking(True)  # Enable mouse tracking
        # Accept right-click events
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
    
    def contextMenuEvent(self, event):
        """Handle context menu event (right-click)"""
        self.context_menu_requested.emit(event.pos())
        event.accept()
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events"""
        self.double_clicked.emit()
        event.accept()
    
    def mousePressEvent(self, event):
        """Handle mouse press events including right-click"""
        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(event.pos())
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self.mouse_moved.emit()
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class SubtitleOverlay(QLabel):
    """Custom widget to display subtitles with styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subtitle_text = ""
        self.style = SubtitleStyle()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
    def set_subtitle(self, text: str):
        """Update subtitle text"""
        self.subtitle_text = text if text else ""
        self.update()
    
    def set_style(self, style: SubtitleStyle):
        """Update subtitle styling"""
        self.style = style
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for styled subtitles"""
        if not self.subtitle_text:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Setup font
        font = QFont(self.style.font_family, self.style.font_size)
        font.setBold(self.style.font_bold)
        font.setItalic(self.style.font_italic)
        painter.setFont(font)
        
        # Get text dimensions
        metrics = painter.fontMetrics()
        lines = self.subtitle_text.split('\n')
        line_height = metrics.height()
        line_rects = [metrics.boundingRect(line) for line in lines]
        line_widths = [rect.width() for rect in line_rects]
        max_width = max(line_widths) if line_widths else 0
        total_height = line_height * len(lines)

        # Vertical anchor
        if self.style.position_vertical == 'bottom':
            y = self.height() - total_height - self.style.margin_vertical
        elif self.style.position_vertical == 'top':
            y = self.style.margin_vertical
        else:  # center
            y = (self.height() - total_height) // 2

        # Block background anchor
        if self.style.position_horizontal == 'center':
            block_x = (self.width() - max_width) // 2
        elif self.style.position_horizontal == 'left':
            block_x = self.style.margin_horizontal
        else:
            block_x = self.width() - max_width - self.style.margin_horizontal

        # Per-line horizontal positions
        line_x_positions = []
        for width in line_widths:
            if self.style.position_horizontal == 'center':
                line_x = (self.width() - width) // 2
            elif self.style.position_horizontal == 'left':
                line_x = self.style.margin_horizontal
            else:
                line_x = self.width() - width - self.style.margin_horizontal
            line_x_positions.append(line_x)
        if not line_x_positions:
            line_x_positions = [block_x]
        
        # Draw background
        if self.style.background_color:
            bg_color = QColor(self.style.background_color)
            painter.fillRect(
                block_x - 10, y - 5,
                max_width + 20, total_height + 10,
                bg_color
            )
        
        # Draw stroke
        if self.style.stroke_width > 0:
            stroke_pen = QPen(QColor(self.style.stroke_color))
            stroke_pen.setWidth(self.style.stroke_width)
            painter.setPen(stroke_pen)
            
            for i, line in enumerate(lines):
                line_y = y + (i + 1) * line_height
                painter.drawText(line_x_positions[i], line_y, line)
        
        # Draw text
        painter.setPen(QColor(self.style.text_color))
        for i, line in enumerate(lines):
            line_y = y + (i + 1) * line_height
            painter.drawText(line_x_positions[i], line_y, line)


class VideoPlayer(QMainWindow):
    """Main video player window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize resource manager first
        from resource_manager import get_resource_manager
        self.resource_manager = get_resource_manager()
        
        self.config_manager = ConfigManager()
        self.subtitle_parser = SubtitleParser()
        self.current_video = None
        self._current_video_source = None
        self.current_subtitles = []
        self.subtitle_style = SubtitleStyle()
        self.subtitle_settings_dialog = None
        self.streaming_stats_dialog = None
        self.playback_rate = 1.0
        self._sample_autoplayed = False
        
        # Background task manager and status footer helpers
        self.task_manager = BackgroundTaskManager()
        self._task_clear_timers = {}
        self._active_tasks_by_key = {}
        self._task_key_lookup = {}
        self.status_footer = None

        # AI generation dialog references
        self.minimized_ai_dialog = None  # Reference to minimized dialog
        self.current_ai_dialog = None  # Reference to current AI dialog (visible or minimized)
        self._ai_progress_slot = None  # Cached slot for thread progress updates

        # Track active translation dialog for quick restore
        self._active_translation_dialog = None
        
        # Auto-hide controls
        self.controls_visible = True
        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setInterval(3000)  # 3 seconds
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_controls)
        
        # VLC setup with suppressed logging
        vlc_args = [
            '--no-xlib',
            '--quiet',
            '--no-video-title-show',
            '--avcodec-hw=none',  # Disable hardware acceleration to avoid errors
            '--no-sub-autodetect-file',  # Don't auto-detect subtitle files
            '--sub-track=-1',  # Disable embedded subtitle tracks
        ]
        self.instance = vlc.Instance(vlc_args)
        self.media_player = self.instance.media_player_new()
        
        # Pass resource manager to casting manager
        self.casting_manager = FFmpegCastingManager(self.resource_manager)
        self.start_cast_action = None
        self.stop_cast_action = None
        
        # Timer for updating UI
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        
        self.init_ui()
        self.apply_theme()
        # Disable sample video autoplay
        # QTimer.singleShot(0, self._autoplay_sample_video)
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("SubtitlePlayer - Professional Video Player")
        self.setGeometry(100, 100, 1200, 700)
        
        # Set focus policy to ensure keyboard events are captured
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        # Splitter for video and sidebar
        self.splitter = SidebarSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #1c1c1c; }")
        self.splitter.splitterMoved.connect(lambda *_: self.update_subtitle_window_geometry())

        # Left side - video container
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_widget.setLayout(left_layout)
        
        # Video frame with subtitle overlay
        self.video_frame = VideoFrame()
        self.video_frame.setMinimumHeight(400)
        
        # Connect signals
        self.video_frame.double_clicked.connect(self.video_double_click)
        self.video_frame.context_menu_requested.connect(self.show_video_context_menu)
        self.video_frame.mouse_moved.connect(self.on_video_mouse_move)
        self.video_frame.resized.connect(self.update_subtitle_window_geometry)
        
        left_layout.addWidget(self.video_frame, stretch=1)

        # Right side - subtitle settings sidebar container
        from subtitle_settings_sidebar import SubtitleSettingsSidebar
        self.sidebar_container = QWidget()
        self.sidebar_container.setMinimumWidth(260)
        self.sidebar_container.setMaximumWidth(480)
        self.sidebar_container.setStyleSheet("background-color: #101010;")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_container.setLayout(sidebar_layout)

        self.subtitle_sidebar = SubtitleSettingsSidebar(self.subtitle_style)
        self.subtitle_sidebar.settings_changed.connect(self.on_sidebar_settings_changed)
        self.subtitle_sidebar.toggle_legacy.connect(self.show_subtitle_settings)
        sidebar_layout.addWidget(self.subtitle_sidebar)

        # Add widgets to splitter
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.sidebar_container)

        # Start with sidebar hidden
        self.sidebar_visible = False
        self.sidebar_container.hide()
        self.subtitle_sidebar.hide()
        self.splitter.setSizes([self.width(), 0])

        # Add splitter to main layout
        main_layout.addWidget(self.splitter, stretch=1)

        # Control panel
        self.control_panel = self.create_control_panel()
        main_layout.addWidget(self.control_panel)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status footer within status bar
        self.status_footer = StatsFooter(self.statusBar())
        self.status_footer.action_requested.connect(self.on_stats_footer_action_requested)
        self.status_footer.cancel_requested.connect(self.on_stats_footer_cancel_requested)
        self.statusBar().addWidget(self.status_footer, 1)
        self.status_footer.set_idle("Ready - Open a video file to begin")
        
        # Resource monitor label
        self.resource_monitor_label = QLabel("")
        self.resource_monitor_label.setStyleSheet("color: #90EE90; font-size: 10px;")
        self.resource_monitor_label.setToolTip("System resource usage")
        self.statusBar().addPermanentWidget(self.resource_monitor_label)
        self.update_resource_monitor()

        # Connect background task manager to footer updates
        self.task_manager.task_started.connect(self.on_background_task_started)
        self.task_manager.task_progress.connect(self.on_background_task_progress)
        self.task_manager.task_completed.connect(self.on_background_task_completed)
        self.task_manager.task_failed.connect(self.on_background_task_failed)
        
        # Timer for resource monitoring (update every 5 seconds)
        self.resource_monitor_timer = QTimer(self)
        self.resource_monitor_timer.setInterval(5000)
        self.resource_monitor_timer.timeout.connect(self.update_resource_monitor)
        self.resource_monitor_timer.start()
        
        # Enable mouse tracking for auto-hide controls
        self.setMouseTracking(True)
        self.video_frame.setMouseTracking(True)
        central_widget.setMouseTracking(True)
        
        # Install event filter to capture ESC key globally
        QApplication.instance().installEventFilter(self)
        
        # Connect VLC to video frame - this embeds the video natively
        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))
        
        # Create a separate window for subtitles that stays on top
        self.create_subtitle_window()
    
    def show_status_message(self, message: str, timeout: int = 0) -> None:
        """Display a transient message in the stats footer."""
        if self.status_footer:
            self.status_footer.show_message(message, timeout)

    def on_stats_footer_action_requested(self, key: str) -> None:
        """Handle action button requests from the stats footer."""
        if key == "ai":
            self.restore_ai_dialog()
        elif key == "translation":
            self.restore_translation_dialog()
        elif key == "casting":
            self.show_streaming_stats()

    def on_stats_footer_cancel_requested(self, key: str) -> None:
        """Handle cancel requests coming from footer status chips."""
        task_id = self._active_tasks_by_key.get(key)
        if task_id:
            self.task_manager.cancel_task(task_id)
            self.show_status_message("Cancelling task...", 2000)
            return

        if key == "translation" and self._active_translation_dialog:
            if hasattr(self._active_translation_dialog, "cancel_translation"):
                self._active_translation_dialog.cancel_translation()
            return

        if key == "casting":
            self.stop_network_cast()

    def restore_translation_dialog(self) -> None:
        """Bring the translation dialog back into focus or reopen it."""
        dialog = self.subtitle_settings_dialog or self._active_translation_dialog
        if dialog and dialog.isVisible():
            dialog.raise_()
            dialog.activateWindow()
        else:
            self.show_subtitle_settings()

    def on_translation_started(self, target_lang: str) -> None:
        """Update footer when translation begins."""
        if self.status_footer:
            self.status_footer.set_status(
                "translation",
                f"🌐 {self._progress_prefix(0)}Translating to {target_lang}",
                button_text="Abrir",
                cancelable=True,
            )
        if self.subtitle_settings_dialog:
            self._active_translation_dialog = self.subtitle_settings_dialog

    def on_translation_progress(self, message: str, percent: int) -> None:
        """Reflect translation progress in footer."""
        if not self.status_footer:
            return

        prefix = "🌐"
        progress_text = self._progress_prefix(percent)
        self.status_footer.set_status(
            "translation",
            f"{prefix} {progress_text}{message}",
            button_text="Abrir",
            cancelable=True,
        )

    def on_translation_finished(self, message: str, success: bool) -> None:
        """Finalize translation status in footer."""
        if not self.status_footer:
            return

        self._active_tasks_by_key.pop("translation", None)

        self.status_footer.set_status(
            "translation",
            f"🌐 {message}",
            button_text="Abrir",
            cancelable=False,
        )

        clear_delay = 8000 if success else 10000
        self.status_footer.schedule_clear("translation", clear_delay)

    def _key_for_task_type(self, task_type: TaskType) -> str:
        if task_type == TaskType.AI_GENERATION:
            return "ai"
        if task_type == TaskType.TRANSLATION:
            return "translation"
        return task_type.value

    def _icon_for_task_type(self, task_type: TaskType) -> str:
        if task_type == TaskType.AI_GENERATION:
            return "🤖"
        if task_type == TaskType.TRANSLATION:
            return "🌐"
        return "⚙️"

    def _progress_prefix(self, percent) -> str:
        if percent is None:
            return ""
        try:
            value = int(percent)
        except (TypeError, ValueError):
            return ""
        value = max(0, min(100, value))
        return f"{value}% - "

    def on_background_task_started(self, task_info: TaskInfo) -> None:
        if not self.status_footer:
            return

        key = self._key_for_task_type(task_info.task_type)
        icon = self._icon_for_task_type(task_info.task_type)
        progress_text = self._progress_prefix(task_info.progress)

        self._active_tasks_by_key[key] = task_info.task_id
        self._task_key_lookup[task_info.task_id] = key

        self.status_footer.set_status(
            key,
            f"{icon} {progress_text}{task_info.message}",
            button_text="Abrir" if key in {"ai", "translation"} else None,
            cancelable=True,
        )

    def on_background_task_progress(self, task_info: TaskInfo) -> None:
        if not self.status_footer:
            return

        key = self._task_key_lookup.get(task_info.task_id)
        if not key:
            return

        icon = self._icon_for_task_type(task_info.task_type)
        progress_text = self._progress_prefix(task_info.progress)

        self.status_footer.set_status(
            key,
            f"{icon} {progress_text}{task_info.message}",
            button_text="Abrir" if key in {"ai", "translation"} else None,
            cancelable=True,
        )

    def on_background_task_completed(self, task_info: TaskInfo) -> None:
        if not self.status_footer:
            return

        key = self._task_key_lookup.pop(task_info.task_id, None)
        if not key:
            return

        self._active_tasks_by_key.pop(key, None)

        icon = self._icon_for_task_type(task_info.task_type)
        message = task_info.message or "Completed!"

        self.status_footer.set_status(
            key,
            f"{icon} {message}",
            button_text="Abrir" if key in {"ai", "translation"} else None,
            cancelable=False,
        )
        self.status_footer.schedule_clear(key, 8000)

    def on_background_task_failed(self, task_info: TaskInfo) -> None:
        if not self.status_footer:
            return

        key = self._task_key_lookup.pop(task_info.task_id, None)
        if not key:
            return

        self._active_tasks_by_key.pop(key, None)

        icon = self._icon_for_task_type(task_info.task_type)
        message = task_info.message or "Failed"

        self.status_footer.set_status(
            key,
            f"{icon} {message}",
            button_text=None,
            cancelable=False,
        )
        self.status_footer.schedule_clear(key, 10000)

    def create_control_panel(self):
        """Create modern video control panel with icons"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(80)
        panel.setMaximumHeight(80)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        panel.setLayout(layout)
        
        # Main controls layout - everything in one line
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Play/Pause button with icon
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_pause_btn.clicked.connect(self.play_pause)
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.setToolTip("Play/Pause (Space)")
        controls_layout.addWidget(self.play_pause_btn)
        
        # Stop button with icon
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setToolTip("Stop")
        controls_layout.addWidget(self.stop_btn)
        
        # Seek backward button
        self.seek_backward_btn = QPushButton()
        self.seek_backward_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekBackward))
        self.seek_backward_btn.clicked.connect(self.seek_backward)
        self.seek_backward_btn.setEnabled(False)
        self.seek_backward_btn.setFixedSize(40, 40)
        self.seek_backward_btn.setToolTip("Seek Backward 10s (←)")
        controls_layout.addWidget(self.seek_backward_btn)
        
        # Seek forward button
        self.seek_forward_btn = QPushButton()
        self.seek_forward_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward))
        self.seek_forward_btn.clicked.connect(self.seek_forward)
        self.seek_forward_btn.setEnabled(False)
        self.seek_forward_btn.setFixedSize(40, 40)
        self.seek_forward_btn.setToolTip("Seek Forward 10s (→)")
        controls_layout.addWidget(self.seek_forward_btn)
        
        # Time label
        self.time_label = QLabel("00:00:00")
        self.time_label.setMinimumWidth(70)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.time_label)
        
        # Timeline slider
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMaximum(1000)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.slider_pressed)
        self.position_slider.sliderReleased.connect(self.slider_released)
        # Enable click-to-seek on timeline
        self.position_slider.mousePressEvent = self.slider_click_seek
        controls_layout.addWidget(self.position_slider)
        
        # Duration label
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setMinimumWidth(70)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.duration_label)
        
        # Volume icon button
        self.volume_btn = QPushButton()
        self.volume_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        self.volume_btn.clicked.connect(self.toggle_mute)
        self.volume_btn.setFixedSize(40, 40)
        self.volume_btn.setToolTip("Mute/Unmute")
        controls_layout.addWidget(self.volume_btn)
        
        # Volume slider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.config_manager.config.volume)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setToolTip("Volume (↑/↓)")
        controls_layout.addWidget(self.volume_slider)
        
        # Volume percentage label
        self.volume_label = QLabel(f"{self.config_manager.config.volume}%")
        self.volume_label.setMinimumWidth(35)
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.volume_label)
        
        # Settings button
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.settings_btn.clicked.connect(self.toggle_subtitle_sidebar)
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setToolTip("Toggle Settings Sidebar")
        controls_layout.addWidget(self.settings_btn)
        
        layout.addLayout(controls_layout)
        
        return panel
    
    def create_subtitle_window(self):
        """Create a transparent floating window for subtitles"""
        self.subtitle_window = QWidget()
        self.subtitle_window.setWindowTitle("Subtitles")
        self.subtitle_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.subtitle_window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.subtitle_window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.subtitle_window.setStyleSheet("background: transparent;")
        
        # Create layout for the overlay
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.subtitle_window.setLayout(layout)
        
        # Add subtitle label - it will handle its own rendering
        self.subtitle_overlay = SubtitleOverlay()
        self.subtitle_overlay.setStyleSheet("background: transparent;")
        self.subtitle_overlay.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.subtitle_overlay.setMinimumSize(10, 10)
        layout.addWidget(self.subtitle_overlay)
        
        # Show window and align with video frame
        self.subtitle_window.show()
        self.update_subtitle_window_geometry()
        QTimer.singleShot(0, self.update_subtitle_window_geometry)

    def _autoplay_sample_video(self):
        """Load and cast the bundled sample video on startup for quick validation."""
        if os.getenv("SUBTITLEPLAYER_DISABLE_SAMPLE_AUTOPLAY") == "1":
            return

        if self._sample_autoplayed or self.current_video:
            return

        sample_path = SAMPLE_VIDEO_PATH
        if not sample_path.exists():
            print(f"[Startup] Sample video not found at {sample_path}")
            return

        self._sample_autoplayed = True

        debug_logger.log_sample_autoplay_started(str(sample_path))

        try:
            self.load_video(str(sample_path), loop=True, source="sample_autoplay")
            self._remove_sample_from_recents(str(sample_path))

            if not self.media_player.is_playing():
                self.play_pause()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[Startup] Failed to load sample video: {exc}")
            return

        self.show_status_message("Sample video ready. Load your own file anytime.", 5000)
        self._start_sample_casting()

    def _remove_sample_from_recents(self, sample_path: str):
        """Avoid persisting the bundled sample in the user's recent files list."""
        try:
            self.config_manager.remove_recent_file(sample_path)
        except AttributeError:
            try:
                if sample_path in getattr(self.config_manager, "recent_files", []):
                    self.config_manager.recent_files.remove(sample_path)
                    self.config_manager.save_recent_files()
            except Exception:  # pylint: disable=broad-except
                pass

    def _start_sample_casting(self):
        """Begin FFmpeg HLS casting for the auto-loaded sample video."""
        if self.casting_manager.is_casting:
            return

        if not self.current_video or not os.path.exists(self.current_video):
            return

        config = FFmpegCastingConfig(host="0.0.0.0", port=8080)

        try:
            url = self.casting_manager.start_hls_stream(self.current_video, config)
        except FFmpegCastingError as exc:
            print(f"[Startup] Unable to start sample casting: {exc}")
            self._update_cast_menu_actions()
            return

        if self.status_footer:
            self.status_footer.set_status("casting", f"📡 Casting ativo: {url}")

        try:
            SAMPLE_CAST_URL_FILE.write_text(url)
            SAMPLE_CAST_LOG_FILE.write_text(f"Sample casting active at {url}\n")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[Startup] Warning: could not persist cast URL: {exc}")

        debug_logger.log_cast_started(
            self.current_video,
            source=self._current_video_source or "sample_autoplay",
            url=url,
            subtitle_path=None,
            autoplay=True,
        )
        print(f"[Startup] Sample HLS casting ready at {url}", flush=True)
        self.show_status_message(f"Sample HLS stream ready at {url}", 5000)
        self._update_cast_menu_actions()

    @staticmethod
    def _resolve_host_ip() -> str:
        """Determine a reachable local IP address for remote clients."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conn:
                conn.connect(("8.8.8.8", 80))
                return conn.getsockname()[0]
        except OSError:
            return "0.0.0.0"
    
    def create_menu_bar(self):
        """Create comprehensive menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Video...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Playback menu
        playback_menu = menubar.addMenu("&Playback")
        
        play_action = QAction("&Play/Pause", self)
        play_action.setShortcut("Space")
        play_action.triggered.connect(self.play_pause)
        playback_menu.addAction(play_action)
        
        stop_action = QAction("&Stop", self)
        stop_action.setShortcut("Ctrl+S")
        stop_action.triggered.connect(self.stop)
        playback_menu.addAction(stop_action)
        
        playback_menu.addSeparator()
        
        seek_forward_action = QAction("Seek &Forward 10s", self)
        seek_forward_action.setShortcut("Right")
        seek_forward_action.triggered.connect(self.seek_forward)
        playback_menu.addAction(seek_forward_action)
        
        seek_backward_action = QAction("Seek &Backward 10s", self)
        seek_backward_action.setShortcut("Left")
        seek_backward_action.triggered.connect(self.seek_backward)
        playback_menu.addAction(seek_backward_action)
        
        playback_menu.addSeparator()
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        playback_menu.addAction(fullscreen_action)
        
        # Audio menu
        audio_menu = menubar.addMenu("&Audio")
        
        volume_up_action = QAction("Volume &Up", self)
        volume_up_action.setShortcut("Up")
        volume_up_action.triggered.connect(lambda: self.adjust_volume(10))
        audio_menu.addAction(volume_up_action)
        
        volume_down_action = QAction("Volume &Down", self)
        volume_down_action.setShortcut("Down")
        volume_down_action.triggered.connect(lambda: self.adjust_volume(-10))
        audio_menu.addAction(volume_down_action)
        
        mute_action = QAction("&Mute/Unmute", self)
        mute_action.setShortcut("M")
        mute_action.triggered.connect(self.toggle_mute)
        audio_menu.addAction(mute_action)
        
        audio_menu.addSeparator()
        
        speed_up_action = QAction("Speed &Increase", self)
        speed_up_action.setShortcut("]")
        speed_up_action.triggered.connect(lambda: self.adjust_playback_speed(0.25))
        audio_menu.addAction(speed_up_action)
        
        speed_down_action = QAction("Speed &Decrease", self)
        speed_down_action.setShortcut("[")
        speed_down_action.triggered.connect(lambda: self.adjust_playback_speed(-0.25))
        audio_menu.addAction(speed_down_action)
        
        reset_speed_action = QAction("&Reset Speed", self)
        reset_speed_action.setShortcut("Backspace")
        reset_speed_action.triggered.connect(self.reset_playback_speed)
        audio_menu.addAction(reset_speed_action)
        
        # Subtitles menu
        subtitle_menu = menubar.addMenu("&Subtitles")
        
        load_subtitle_action = QAction("&Load Subtitle File...", self)
        load_subtitle_action.setShortcut("Ctrl+L")
        load_subtitle_action.triggered.connect(self.open_subtitle)
        subtitle_menu.addAction(load_subtitle_action)
        
        download_action = QAction("&Download Subtitles...", self)
        download_action.setShortcut("Ctrl+D")
        download_action.triggered.connect(self.show_subtitle_search)
        subtitle_menu.addAction(download_action)
        
        ai_gen_action = QAction("&Generate Subtitles (AI)...", self)
        ai_gen_action.setShortcut("Ctrl+G")
        ai_gen_action.triggered.connect(self.show_ai_subtitle_generator)
        subtitle_menu.addAction(ai_gen_action)
        
        subtitle_menu.addSeparator()
        
        settings_action = QAction("Subtitle &Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_subtitle_settings)
        subtitle_menu.addAction(settings_action)
        
        sidebar_action = QAction("Toggle Settings Si&debar", self)
        sidebar_action.setShortcut("Ctrl+B")
        sidebar_action.triggered.connect(self.toggle_subtitle_sidebar)
        subtitle_menu.addAction(sidebar_action)

        # Cast menu
        cast_menu = menubar.addMenu("&Cast")

        self.start_cast_action = QAction("&Start HTTP Cast...", self)
        self.start_cast_action.setShortcut("Ctrl+Shift+C")
        self.start_cast_action.triggered.connect(self.start_network_cast)
        cast_menu.addAction(self.start_cast_action)

        self.stop_cast_action = QAction("St&op Cast", self)
        self.stop_cast_action.setShortcut("Ctrl+Shift+X")
        self.stop_cast_action.triggered.connect(self.stop_network_cast)
        cast_menu.addAction(self.stop_cast_action)
        
        cast_menu.addSeparator()
        
        analytics_action = QAction("Streaming &Analytics...", self)
        analytics_action.triggered.connect(self.show_streaming_stats)
        cast_menu.addAction(analytics_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self._update_cast_menu_actions()

    def _update_cast_menu_actions(self):
        """Enable or disable cast menu actions based on state."""
        casting = self.casting_manager.is_casting
        can_start = bool(self.current_video and os.path.exists(self.current_video))

        if self.start_cast_action is not None:
            self.start_cast_action.setEnabled(can_start and not casting)
        if self.stop_cast_action is not None:
            self.stop_cast_action.setEnabled(casting)
    
    def show_streaming_stats(self):
        """Open the streaming analytics dialog."""
        if self.streaming_stats_dialog is None:
            self.streaming_stats_dialog = StreamingStatsDialog(self)
            self.streaming_stats_dialog.finished.connect(self._on_streaming_stats_closed)

        self.streaming_stats_dialog.refresh()
        self.streaming_stats_dialog.exec()

    def _on_streaming_stats_closed(self, _result: int) -> None:
        """Reset the dialog reference after it closes."""
        if self.streaming_stats_dialog is not None:
            # Ensure the widget is deleted to release resources.
            self.streaming_stats_dialog.deleteLater()
            self.streaming_stats_dialog = None

    def update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.clear()
        
        for filepath in self.config_manager.recent_files:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                action = QAction(filename, self)
                action.setData(filepath)
                action.triggered.connect(
                    lambda checked, path=filepath: self.load_video(path, source="recent_file")
                )
                self.recent_menu.addAction(action)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QFrame {
                background-color: #2d2d2d;
                border: none;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #7d7d7d;
            }
            QLabel {
                color: #cccccc;
                font-size: 13px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #3d3d3d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0e639c;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1177bb;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #cccccc;
            }
            QMenuBar::item:selected {
                background-color: #0e639c;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #cccccc;
            }
        """)
    
    def open_file(self):
        """Open video file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv *.m4v *.webm);;All Files (*.*)"
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, file_path: str, *, loop: bool = False, source: str = "user"):
        """Load and play video file"""
        previous_video = self.current_video
        previous_source = getattr(self, "_current_video_source", None)

        self.current_video = file_path
        self._current_video_source = source

        debug_logger.log_video_loaded(file_path, source=source, loop=loop)

        if self.casting_manager.is_casting:
            if previous_video:
                debug_logger.log_cast_stopped(
                    previous_video,
                    source=previous_source,
                    reason="video_changed",
                )
            self.casting_manager.stop()
            if self.status_footer:
                self.status_footer.clear_status("casting")
            self.show_status_message("Casting stopped for new video", 3000)
        self._update_cast_menu_actions()
        
        # Add to recent files
        self.config_manager.add_recent_file(file_path)
        self.update_recent_menu()
        
        # Load video
        media = self.instance.media_new(file_path)
        if loop:
            media.add_option(":input-repeat=-1")
        self.media_player.set_media(media)
        
        # Enable controls
        self.play_pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.seek_forward_btn.setEnabled(True)
        self.seek_backward_btn.setEnabled(True)
        
        # Try to auto-load subtitle
        subtitle_file = self.config_manager.get_subtitle_file_for_video(file_path)
        if subtitle_file and os.path.exists(subtitle_file):
            print(f"[Subtitle] Loading saved association: {os.path.basename(subtitle_file)}")
            self.load_subtitle(subtitle_file)
        else:
            # Check for subtitle file in same directory with multiple patterns
            video_path = Path(file_path)
            video_name = video_path.stem
            video_dir = video_path.parent
            
            # Search patterns (in order of preference)
            patterns = [
                # Exact name match (most common)
                lambda ext: video_path.with_suffix(ext),
                # Language codes (e.g., movie.en.srt, movie.pt-BR.srt)
                lambda ext: video_dir / f"{video_name}.en{ext}",
                lambda ext: video_dir / f"{video_name}.pt-BR{ext}",
                lambda ext: video_dir / f"{video_name}.pt{ext}",
                lambda ext: video_dir / f"{video_name}.es{ext}",
                # Common suffixes
                lambda ext: video_dir / f"{video_name}.eng{ext}",
                lambda ext: video_dir / f"{video_name}.por{ext}",
            ]
            
            for ext in ['.srt', '.vtt', '.ass', '.ssa']:
                for pattern in patterns:
                    sub_path = pattern(ext)
                    if sub_path.exists():
                        print(f"[Subtitle] Auto-detected: {sub_path.name}")
                        self.load_subtitle(str(sub_path))
                        break
                else:
                    continue  # Continue outer loop if inner didn't break
                break  # Break outer loop if subtitle was found
        
        # Load subtitle style
        self.subtitle_style = self.config_manager.load_subtitle_style(file_path)
        self.subtitle_overlay.set_style(self.subtitle_style)
        
        # Start playing
        self.media_player.play()
        self.timer.start()
        
        self.show_status_message(f"Playing: {os.path.basename(file_path)}")
        self._update_cast_menu_actions()
    
    def open_subtitle(self):
        """Open subtitle file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Subtitle File",
            "",
            "Subtitle Files (*.srt *.vtt *.ass *.ssa);;All Files (*.*)"
        )
        
        if file_path:
            self.load_subtitle(file_path)
    
    def load_subtitle(self, file_path: str):
        """Load subtitle file"""
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found", f"Subtitle file not found:\n{file_path}")
                return
            
            # Parse subtitle file
            self.current_subtitles = self.subtitle_parser.parse_file(file_path)
            
            if self.current_subtitles:
                # Apply timing offset if set
                if self.subtitle_style.timing_offset != 0:
                    self.current_subtitles = self.subtitle_parser.adjust_timing(
                        self.current_subtitles,
                        self.subtitle_style.timing_offset
                    )
                
                # Save association with current video
                if self.current_video:
                    self.config_manager.set_subtitle_file_for_video(self.current_video, file_path)
                    print(f"✓ Saved subtitle association: {os.path.basename(self.current_video)} → {os.path.basename(file_path)}")
                    try:
                        debug_logger.log_subtitle_linked(self.current_video, file_path)
                    except Exception:  # pylint: disable=broad-except
                        pass
                
                # Update status with subtitle count
                subtitle_count = len(self.current_subtitles)
                self.show_status_message(
                    f"✓ Loaded {subtitle_count} subtitles from: {os.path.basename(file_path)}"
                )
                
                # Log for debugging
                print(f"✓ Loaded {subtitle_count} subtitles from: {file_path}")
            else:
                QMessageBox.warning(
                    self, 
                    "Parse Error", 
                    f"Could not parse subtitle file:\n{os.path.basename(file_path)}\n\n"
                    "Supported formats: SRT, VTT, ASS, SSA"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Subtitles",
                f"An error occurred while loading subtitles:\n\n{str(e)}"
            )
            print(f"✗ Error loading subtitles: {e}")
    
    def play_pause(self):
        """Toggle play/pause"""
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.mouse_move_timer.stop()  # Stop auto-hide when paused
            self.show_controls()  # Show controls when paused
        else:
            self.media_player.play()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.timer.start()
            self.mouse_move_timer.start()  # Start auto-hide when playing
    
    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.timer.stop()
        self.mouse_move_timer.stop()  # Stop auto-hide when stopped
        self.show_controls()  # Show controls when stopped
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.position_slider.setValue(0)
        self.subtitle_overlay.set_subtitle("")
    
    def seek_forward(self):
        """Seek forward 10 seconds"""
        if self.media_player.get_length() > 0:
            current_time = self.media_player.get_time()  # milliseconds
            new_time = current_time + 10000  # Add 10 seconds
            self.media_player.set_time(new_time)
    
    def seek_backward(self):
        """Seek backward 10 seconds"""
        if self.media_player.get_length() > 0:
            current_time = self.media_player.get_time()  # milliseconds
            new_time = max(0, current_time - 10000)  # Subtract 10 seconds, but not below 0
            self.media_player.set_time(new_time)
    
    def toggle_mute(self):
        """Toggle mute/unmute"""
        muted = self.media_player.audio_get_mute()
        self.media_player.audio_set_mute(not muted)
        self.show_status_message("Audio muted" if not muted else "Audio unmuted", 2000)
        if not muted:
            # Muting
            self.volume_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
            self.volume_btn.setToolTip("Unmute")
        else:
            # Unmuting
            self.volume_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
            self.volume_btn.setToolTip("Mute")
    
    def set_position(self, position):
        """Set playback position from slider"""
        self.media_player.set_position(position / 1000.0)
    
    def slider_pressed(self):
        """Handle slider press"""
        self.timer.stop()
    def slider_released(self):
        """Handle slider release"""
        if self.media_player.is_playing():
            self.timer.start()
    
    def slider_click_seek(self, event):
        """Handle click anywhere on slider to seek"""
        # Calculate position based on click location
        slider_width = self.position_slider.width()
        click_position = event.position().x()
        value = int((click_position / slider_width) * self.position_slider.maximum())
        
        # Set slider and seek video
        self.position_slider.setValue(value)
        self.set_position(value)
        
        # Call original mouse press event for drag functionality
        QSlider.mousePressEvent(self.position_slider, event)
    
    def set_volume(self, volume):
        """Set playback volume"""
        self.media_player.audio_set_volume(volume)
        self.volume_label.setText(f"{volume}%")
        self.config_manager.config.volume = volume
        self.config_manager.save_config()
    
    def update_ui(self):
        """Update UI elements (called by timer)"""
        # Update position slider
        media_pos = int(self.media_player.get_position() * 1000)
        self.position_slider.setValue(media_pos)
        
        # Update time labels (convert milliseconds to seconds)
        current_time_ms = self.media_player.get_time()  # milliseconds
        duration_ms = self.media_player.get_length()  # milliseconds
        
        current_time_sec = current_time_ms // 1000  # for display
        duration_sec = duration_ms // 1000  # for display
        
        self.time_label.setText(self.format_time(current_time_sec))
        self.duration_label.setText(self.format_time(duration_sec))
        
        # Update subtitles (need time in seconds with decimal)
        if self.current_subtitles and current_time_ms >= 0:
            current_time_float = current_time_ms / 1000.0  # Convert to seconds with decimal
            subtitle_text = self.subtitle_parser.get_subtitle_at_time(
                self.current_subtitles,
                current_time_float
            )
            self.subtitle_overlay.set_subtitle(subtitle_text or "")
    
    def format_time(self, seconds):
        """Format time in HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode with proper escape handling"""
        if self.isFullScreen():
            self.showNormal()
            # Force show all controls when exiting fullscreen
            self.menuBar().show()
            self.statusBar().show()
            self.control_panel.show()
            self.controls_visible = True
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Stop auto-hide timer when exiting fullscreen
            self.mouse_move_timer.stop()
        else:
            self.showFullScreen()
            # Ensure window has focus for keyboard events
            self.setFocus()
            self.activateWindow()
            # Start auto-hide timer if playing
            if self.media_player.is_playing():
                self.mouse_move_timer.start()
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement to show controls"""
        self.show_controls()
        self.mouse_move_timer.start()  # Restart the timer
        super().mouseMoveEvent(event)
    
    def on_video_mouse_move(self):
        """Handle mouse movement over video frame"""
        self.show_controls()
        if self.media_player.is_playing():
            self.mouse_move_timer.start()  # Restart the timer
    
    def show_controls(self):
        """Show menu bar, status bar, and control panel"""
        self.menuBar().show()
        self.statusBar().show()
        self.control_panel.show()
        self.controls_visible = True
        # Show cursor
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def hide_controls(self):
        """Hide menu bar, status bar, and control panel (only when playing)"""
        # Only hide controls if playing
        if not self.media_player.is_playing():
            return
            
        if not self.controls_visible:
            return
            
        # Don't hide if mouse is over controls or sidebar is visible
        mouse_pos = self.mapFromGlobal(self.cursor().pos())
        if self.control_panel.geometry().contains(mouse_pos):
            # Mouse is over controls, restart timer
            self.mouse_move_timer.start()
            return
        
        # Hide controls based on mode
        if self.sidebar_visible:
            # Don't hide menu/status when sidebar is visible, only control panel
            self.control_panel.hide()
        else:
            # Hide everything for immersive experience
            self.menuBar().hide()
            self.statusBar().hide()
            self.control_panel.hide()
        
        self.controls_visible = False
        # Hide cursor for immersive experience
        self.setCursor(Qt.CursorShape.BlankCursor)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Show controls on any key press
        self.show_controls()
        self.mouse_move_timer.start()
        
        # ESC key exits fullscreen - ALWAYS prioritize this
        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.toggle_fullscreen()
                event.accept()  # Mark event as handled
                return
        # F key toggles fullscreen
        elif event.key() == Qt.Key.Key_F:
            self.toggle_fullscreen()
            event.accept()
            return
        # Space bar plays/pauses
        elif event.key() == Qt.Key.Key_Space:
            self.play_pause()
            event.accept()
            return
        # Menu key or Shift+F10 opens context menu
        elif event.key() == Qt.Key.Key_Menu or (event.key() == Qt.Key.Key_F10 and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            # Show context menu at center of video frame
            center = self.video_frame.rect().center()
            self.show_video_context_menu(center)
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    def eventFilter(self, obj, event):
        """Global event filter to catch ESC key in fullscreen"""
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
                self.toggle_fullscreen()
                return True
        return super().eventFilter(obj, event)
    
    def video_double_click(self, event):
        """Handle double-click on video frame to toggle fullscreen"""
        self.toggle_fullscreen()
    
    def show_video_context_menu(self, position):
        """Show comprehensive context menu on right-click"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 25px 5px 25px;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3d3d3d;
                margin: 5px 0px;
            }
        """)
        
        # File operations
        open_action = menu.addAction("📁 Open Video...")
        open_action.triggered.connect(self.open_file)
        
        menu.addSeparator()
        
        # Playback actions
        if self.media_player.is_playing():
            play_action = menu.addAction("⏸ Pause")
            play_action.triggered.connect(self.play_pause)
        else:
            play_action = menu.addAction("▶ Play")
            play_action.triggered.connect(self.play_pause)
        
        stop_action = menu.addAction("⏹ Stop")
        stop_action.triggered.connect(self.stop)
        
        menu.addSeparator()
        
        # Seek controls
        seek_forward_action = menu.addAction("⏩ Seek Forward 10s")
        seek_forward_action.triggered.connect(self.seek_forward)
        seek_forward_action.setEnabled(self.current_video is not None)
        
        seek_backward_action = menu.addAction("⏪ Seek Backward 10s")
        seek_backward_action.triggered.connect(self.seek_backward)
        seek_backward_action.setEnabled(self.current_video is not None)
        
        menu.addSeparator()
        
        # Audio controls
        volume_up_action = menu.addAction("🔊 Volume +10%")
        volume_up_action.triggered.connect(lambda: self.adjust_volume(10))

        volume_down_action = menu.addAction("🔉 Volume -10%")
        volume_down_action.triggered.connect(lambda: self.adjust_volume(-10))

        mute_action = menu.addAction("🔇 Toggle Mute")
        mute_action.triggered.connect(self.toggle_mute)

        menu.addSeparator()

        # Playback speed controls
        faster_action = menu.addAction("⚡ Speed +0.25x")
        faster_action.triggered.connect(lambda: self.adjust_playback_speed(0.25))

        slower_action = menu.addAction("🐌 Speed -0.25x")
        slower_action.triggered.connect(lambda: self.adjust_playback_speed(-0.25))

        reset_speed_action = menu.addAction("⏯ Reset Speed (1.0x)")
        reset_speed_action.triggered.connect(self.reset_playback_speed)

        menu.addSeparator()

        # Subtitle actions
        load_sub_action = menu.addAction("📄 Load Subtitle File...")
        load_sub_action.triggered.connect(self.open_subtitle)
        
        download_sub_action = menu.addAction("⬇ Download Subtitles...")
        download_sub_action.triggered.connect(self.show_subtitle_search)
        download_sub_action.setEnabled(self.current_video is not None)
        
        ai_action = menu.addAction("🤖 Generate Subtitles (AI)...")
        ai_action.triggered.connect(self.show_ai_subtitle_generator)
        ai_action.setEnabled(self.current_video is not None)
        
        menu.addSeparator()
        
        # Settings
        sidebar_action = menu.addAction("⚙ Settings Sidebar")
        sidebar_action.triggered.connect(self.toggle_subtitle_sidebar)

        legacy_action = menu.addAction("🔧 Legacy Settings Dialog...")
        legacy_action.triggered.connect(self.show_subtitle_settings)

        menu.addSeparator()
        
        # Casting controls
        if self.casting_manager.is_casting:
            stop_cast_action = menu.addAction("� Stop Network Cast")
            stop_cast_action.triggered.connect(self.stop_network_cast)
            url = self.casting_manager.url or "(unknown)"
            url_action = menu.addAction(f"🔗 {url}")
            url_action.setEnabled(False)
        else:
            start_cast_action = menu.addAction("🛰 Start Network Cast...")
            start_cast_action.setEnabled(self.current_video is not None)
            start_cast_action.triggered.connect(self.start_network_cast)
        
        analytics_action = menu.addAction("📊 Streaming Analytics...")
        analytics_action.triggered.connect(self.show_streaming_stats)

        menu.addSeparator()

        # Fullscreen
        if self.isFullScreen():
            fullscreen_action = menu.addAction("⊡ Exit Fullscreen")
        else:
            fullscreen_action = menu.addAction("⛶ Fullscreen")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
        # Show menu at cursor position
        menu.exec(self.video_frame.mapToGlobal(position))

    def ensure_sidebar_visible(self):
        """Ensure the sidebar is visible without toggling off inadvertently"""
        if not self.sidebar_visible:
            self.toggle_subtitle_sidebar()
        else:
            self.sidebar_container.show()
            self.subtitle_sidebar.show()
        self.update_subtitle_window_geometry()

    def adjust_volume(self, delta):
        """Adjust master volume by delta percent"""
        current_volume = self.media_player.audio_get_volume()
        if current_volume == -1:
            current_volume = self.volume_slider.value()
        new_volume = max(0, min(100, current_volume + delta))
        self.volume_slider.setValue(new_volume)
        self.set_volume(new_volume)
        self.show_status_message(f"Volume set to {new_volume}%", 2000)

    def toggle_mute(self):
        """Toggle audio mute state"""
        muted = self.media_player.audio_get_mute()
        self.media_player.audio_set_mute(not muted)
        self.show_status_message("Audio muted" if not muted else "Audio unmuted", 2000)

    def adjust_playback_speed(self, delta):
        """Adjust playback speed by delta"""
        new_rate = max(0.25, min(4.0, self.playback_rate + delta))
        if abs(new_rate - self.playback_rate) < 1e-3:
            return
        if self.media_player.set_rate(new_rate) == 0:
            self.playback_rate = new_rate
            self.show_status_message(f"Playback speed: {self.playback_rate:.2f}x", 2000)
        else:
            self.show_status_message("Unable to change playback speed", 2000)

    def reset_playback_speed(self):
        """Reset playback speed to normal"""
        if self.media_player.set_rate(1.0) == 0:
            self.playback_rate = 1.0
            self.show_status_message("Playback speed reset to 1.00x", 2000)

    def start_network_cast(self):
        """Start casting the current media over HTTP using FFmpeg HLS."""
        if not self.current_video:
            QMessageBox.information(
                self,
                "No Video",
                "Load a video before starting a casting session."
            )
            self._update_cast_menu_actions()
            debug_logger.log_cast_failed(
                None,
                source=self._current_video_source,
                error="no_current_video",
            )
            return

        if self.casting_manager.is_casting:
            debug_logger.log_cast_stopped(
                self.current_video,
                source=self._current_video_source,
                reason="restart_requested",
            )
            self.casting_manager.stop()
            if self.status_footer:
                self.status_footer.clear_status("casting")
            self.show_status_message("Restarting cast for current video", 3000)
        self._update_cast_menu_actions()

        if not os.path.exists(self.current_video):
            QMessageBox.warning(
                self,
                "Video Not Found",
                f"Video file not found:\n{self.current_video}"
            )
            self._update_cast_menu_actions()
            debug_logger.log_cast_failed(
                self.current_video,
                source=self._current_video_source,
                error="video_missing",
            )
            return

        subtitle_path = None
        if self.current_video:
            subtitle_path = self.config_manager.get_subtitle_file_for_video(self.current_video)
            if subtitle_path and not os.path.exists(subtitle_path):
                print(f"[Casting] Subtitle file missing for cast: {subtitle_path}")
                subtitle_path = None

        try:
            config = FFmpegCastingConfig(host="0.0.0.0", port=8080)
            url = self.casting_manager.start_hls_stream(
                self.current_video,
                config,
                subtitle_path=subtitle_path,
            )
        except FFmpegCastingError as exc:
            self._update_cast_menu_actions()
            QMessageBox.critical(
                self,
                "Casting Failed",
                f"Unable to start network casting.\n\n{exc}"
            )
            debug_logger.log_cast_failed(
                self.current_video,
                source=self._current_video_source,
                error=str(exc),
            )
            return

        if self.status_footer:
            self.status_footer.set_status("casting", f"📡 Casting ativo: {url}")
        self.show_status_message(f"Casting started: {url}", 5000)
        debug_logger.log_cast_started(
            self.current_video,
            source=self._current_video_source,
            url=url,
            subtitle_path=subtitle_path,
            autoplay=False,
        )
        self._update_cast_menu_actions()
        QMessageBox.information(
            self,
            "Casting Started",
            "HLS streaming started successfully.\n\n"
            f"Access from mobile device:\n{url}\n\n"
            f"Compatible with:\n"
            f"• VLC for Android/iOS\n"
            f"• MX Player\n"
            f"• Modern web browsers\n\n"
            f"Subtitles loaded for casting: {'Yes' if subtitle_path else 'No'}"
        )

    def stop_network_cast(self):
        """Stop the active casting session."""
        if not self.casting_manager.is_casting:
            self.show_status_message("No active casting session", 2000)
            self._update_cast_menu_actions()
            return

        self.casting_manager.stop()
        debug_logger.log_cast_stopped(
            self.current_video,
            source=self._current_video_source,
            reason="user_requested",
        )
        if self.status_footer:
            self.status_footer.clear_status("casting")
        self.show_status_message("Casting stopped", 3000)
        QMessageBox.information(
            self,
            "Casting Stopped",
            "Network casting has been stopped."
        )
        self._update_cast_menu_actions()
    
    def show_subtitle_search(self):
        """Show subtitle search dialog"""
        # Import here to avoid circular dependency
        from subtitle_search_dialog import SubtitleSearchDialog
        
        if not self.current_video:
            QMessageBox.information(self, "No Video", "Please load a video first")
            return
        
        dialog = SubtitleSearchDialog(self.current_video, self)
        if dialog.exec():
            subtitle_path = dialog.get_selected_subtitle_path()
            if subtitle_path:
                self.load_subtitle(subtitle_path)
    
    def toggle_subtitle_sidebar(self):
        """Toggle the visibility of the subtitle settings sidebar"""
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.sidebar_container.show()
            self.subtitle_sidebar.show()
            sidebar_width = max(320, int(self.width() * 0.28))
            self.splitter.setSizes([max(1, self.width() - sidebar_width), sidebar_width])
            if self.subtitle_settings_dialog and self.subtitle_settings_dialog.isVisible():
                self.subtitle_settings_dialog.reject()
        else:
            self.sidebar_container.hide()
            self.subtitle_sidebar.hide()
            self.splitter.setSizes([self.width(), 0])
        self.update_subtitle_window_geometry()
    
    def on_sidebar_settings_changed(self, style):
        """Handle changes from subtitle settings sidebar"""
        self.subtitle_style = style
        self.subtitle_overlay.set_style(self.subtitle_style)
    
    def update_resource_monitor(self):
        """Update resource usage display in status bar"""
        try:
            usage_str = self.resource_manager.get_resource_usage_string()
            
            # Add GPU info if available
            if self.resource_manager.resources.use_gpu:
                gpu_name = self.resource_manager.resources.gpu.name.split()[0]  # First word (e.g., "RTX")
                usage_str = f"🚀 {gpu_name} | {usage_str}"
            else:
                usage_str = f"💻 CPU | {usage_str}"
            
            self.resource_monitor_label.setText(usage_str)
        except Exception as e:
            # Silently fail - resource monitoring is not critical
            pass
    
    def on_task_indicator_clicked(self, task_id: str):
        """Handle click on task indicator - restore associated dialog"""
        task_info = self.task_manager.get_task_info(task_id)
        if not task_info:
            return
        
        from background_task_manager import TaskType
        
        # Try to restore the associated dialog
        if task_info.task_type == TaskType.AI_GENERATION:
            # Check if AI dialog exists and restore it
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QDialog) and widget.windowTitle().startswith("AI Subtitle Generator"):
                    if hasattr(widget, 'restore_from_background'):
                        widget.restore_from_background()
                        return
        
        # If dialog not found, show info
        QMessageBox.information(
            self,
            "Background Task",
            f"Task is running in background:\n{task_info.message}"
        )
    
    def on_task_cancel_requested(self, task_id: str):
        """Handle cancel request from status indicator"""
        reply = QMessageBox.question(
            self,
            "Cancel Task?",
            "Are you sure you want to cancel this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.task_manager.cancel_task(task_id)
    
    def show_subtitle_settings(self):
        """Show subtitle settings dialog"""
        # Import here to avoid circular dependency
        from subtitle_settings_dialog import SubtitleSettingsDialog

        if self.subtitle_settings_dialog and self.subtitle_settings_dialog.isVisible():
            self.subtitle_settings_dialog.raise_()
            self.subtitle_settings_dialog.activateWindow()
            return
        
        if self.sidebar_visible:
            self.sidebar_visible = False
            self.sidebar_container.hide()
            self.subtitle_sidebar.hide()
            self.splitter.setSizes([self.width(), 0])

        # Get current subtitle file path
        subtitle_path = None
        if self.current_video:
            subtitle_path = self.config_manager.get_subtitle_file_for_video(self.current_video)
        
        dialog = SubtitleSettingsDialog(
            self.subtitle_style,
            self,
            subtitles=self.current_subtitles,
            current_time_func=lambda: self.media_player.get_time() / 1000.0,
            video_path=self.current_video,
            subtitle_path=subtitle_path
        )
        dialog.setModal(False)
        dialog.toggle_sidebar_requested.connect(self.toggle_subtitle_sidebar)
        dialog.translation_started.connect(self.on_translation_started)
        dialog.translation_progress.connect(self.on_translation_progress)
        dialog.translation_finished.connect(self.on_translation_finished)
        dialog.finished.connect(lambda result, dlg=dialog: self._on_subtitle_dialog_finished(dlg, result))
        self.subtitle_settings_dialog = dialog
        self._active_translation_dialog = dialog

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    
    def show_ai_subtitle_generator(self):
        """Show AI subtitle generation dialog"""
        if not self.current_video:
            QMessageBox.information(self, "No Video", "Please load a video first")
            return
        
        # Check if there's already a dialog in progress (minimized or visible)
        if self.minimized_ai_dialog:
            self.restore_ai_dialog()
            return
        
        if self.current_ai_dialog and self.current_ai_dialog.isVisible():
            self.current_ai_dialog.raise_()
            self.current_ai_dialog.activateWindow()
            return
        
        try:
            from ai_subtitle_dialog import AISubtitleDialog
            from ai_subtitle_generator import AISubtitleGenerator
            
            # Pass task_manager and resource_manager for background mode and optimization
            dialog = AISubtitleDialog(self.current_video, self, self.task_manager)
            
            # Store dialog reference
            self.current_ai_dialog = dialog
            
            # Connect to dialog events
            dialog.finished.connect(lambda result: self.on_ai_dialog_finished(dialog, result))
            dialog.minimized_to_background.connect(lambda: self.on_ai_dialog_minimized(dialog))
            
            # Show dialog
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        except ImportError as e:
            QMessageBox.warning(
                self,
                "Dependencies Missing",
                "AI subtitle generation requires additional dependencies.\n\n"
                "Install with:\n"
                "pip install openai-whisper torch\n\n"
                "See Subtitles > Generate Subtitles (AI) for details."
            )
    
    def on_ai_dialog_finished(self, dialog, result):
        """Handle AI dialog finished (accepted or rejected)"""
        if result and dialog.generated_segments:
            from ai_subtitle_generator import AISubtitleGenerator
            segments = dialog.get_generated_segments()
            subtitle_path = dialog.get_subtitle_path()
            generator = AISubtitleGenerator(resource_manager=self.resource_manager)
            if generator.save_to_srt(segments, subtitle_path):
                # Load the generated subtitle
                self.load_subtitle(subtitle_path)
                QMessageBox.information(
                    self,
                    "Success",
                    f"AI-generated subtitles saved and loaded!\n{subtitle_path}"
                )
        
        # Clean up all references
        self.current_ai_dialog = None
        self.minimized_ai_dialog = None

        # Disconnect any remaining progress handlers
        if hasattr(dialog, 'gen_thread') and dialog.gen_thread:
            if self._ai_progress_slot:
                try:
                    dialog.gen_thread.progress_update.disconnect(self._ai_progress_slot)
                except TypeError:
                    pass
            try:
                dialog.gen_thread.finished.disconnect(self.on_ai_generation_finished)
            except TypeError:
                pass
        self._ai_progress_slot = None

        if self.status_footer:
            self.status_footer.clear_status("ai")
    
    def on_ai_dialog_minimized(self, dialog):
        """Handle AI dialog minimized to background"""
        # Store reference to dialog
        self.minimized_ai_dialog = dialog

        # Get current progress from dialog
        current_progress = dialog.progress_bar.value()
        current_message = dialog.status_label.text()
        
        # Check if generation is already complete
        generation_complete = not (hasattr(dialog, 'gen_thread') and 
                                   dialog.gen_thread and 
                                   dialog.gen_thread.isRunning())
        if self.status_footer:
            if generation_complete:
                status_text = "🤖 100% - Complete! Clique para abrir"
            else:
                status_text = f"🤖 {current_progress}% - {current_message}"
            self.status_footer.set_status(
                "ai",
                status_text,
                button_text="Abrir",
            )

        # Keep player window active so keyboard shortcuts remain usable
        self.activateWindow()
        self.raise_()

        # Connect progress updates from thread directly to footer (only if running)
        if hasattr(dialog, 'gen_thread') and dialog.gen_thread and dialog.gen_thread.isRunning():
            if self._ai_progress_slot is None:
                def _ai_progress_slot(message, percent):
                    if self.status_footer:
                        self.status_footer.set_status(
                            "ai",
                            f"🤖 {percent}% - {message}",
                            button_text="Abrir",
                        )

                self._ai_progress_slot = _ai_progress_slot

            try:
                dialog.gen_thread.progress_update.connect(
                    self._ai_progress_slot,
                    Qt.ConnectionType.UniqueConnection,
                )
            except TypeError:
                pass  # Already connected

            try:
                dialog.gen_thread.finished.connect(
                    self.on_ai_generation_finished,
                    Qt.ConnectionType.UniqueConnection,
                )
            except TypeError:
                pass
    
    def restore_ai_dialog(self):
        """Restore minimized AI dialog"""
        if self.minimized_ai_dialog:
            # Use the dialog's restore method to ensure proper rendering
            self.minimized_ai_dialog.restore_from_background()

            if self.status_footer:
                self.status_footer.clear_status("ai")
            
            # DON'T clear minimized_ai_dialog here - keep it so we can minimize again!
            # It will be cleared when generation finishes or dialog is closed
    
    def on_ai_generation_finished(self):
        """Handle AI generation completion"""
        if self.minimized_ai_dialog and self.status_footer:
            self.status_footer.set_status(
                "ai",
                "🤖 100% - Complete! Clique para abrir",
                button_text="Abrir",
            )

        # Disconnect progress slot once generation completes
        dialog = self.current_ai_dialog or self.minimized_ai_dialog
        if dialog and hasattr(dialog, 'gen_thread') and dialog.gen_thread:
            if self._ai_progress_slot:
                try:
                    dialog.gen_thread.progress_update.disconnect(self._ai_progress_slot)
                except TypeError:
                    pass
            try:
                dialog.gen_thread.finished.disconnect(self.on_ai_generation_finished)
            except TypeError:
                pass

        self._ai_progress_slot = None
        
        # Keep references so user can still open the completed dialog
        # They will be cleared when dialog is actually closed
    
    def _on_subtitle_dialog_finished(self, dialog: QDialog, result: int) -> None:
        """Handle legacy subtitle dialog completion without blocking UI."""
        if dialog is not self.subtitle_settings_dialog:
            return

        try:
            if result == int(QDialog.DialogCode.Accepted):
                self.subtitle_style = dialog.get_style()
                self.subtitle_overlay.set_style(self.subtitle_style)

                if self.current_subtitles:
                    base_path = self.config_manager.get_subtitle_file_for_video(self.current_video)
                    if base_path and os.path.exists(base_path):
                        base_subtitles = self.subtitle_parser.parse_file(base_path)
                        self.current_subtitles = self.subtitle_parser.adjust_timing(
                            base_subtitles,
                            self.subtitle_style.timing_offset
                        )

                if self.current_video:
                    self.config_manager.save_subtitle_style(self.subtitle_style, self.current_video)
        finally:
            self._clear_subtitle_dialog_reference()
            dialog.deleteLater()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SubtitlePlayer",
            "<h3>SubtitlePlayer v1.0</h3>"
            "<p>A professional video player with native subtitle download support.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Support for multiple video formats</li>"
            "<li>Native OpenSubtitles.com integration</li>"
            "<li>Customizable subtitle styling</li>"
            "<li>Modern, professional interface</li>"
            "</ul>"
            "<p>© 2025 SubtitlePlayer Project</p>"
        )

    def _clear_subtitle_dialog_reference(self):
        """Reset legacy dialog reference when it closes"""
        self.subtitle_settings_dialog = None
        self._active_translation_dialog = None

    def update_subtitle_window_geometry(self):
        """Synchronize subtitle overlay window with the video frame"""
        if not hasattr(self, 'subtitle_window') or not hasattr(self, 'video_frame'):
            return

        video_rect = self.video_frame.rect()
        global_pos = self.video_frame.mapToGlobal(QPoint(0, 0))

        self.subtitle_window.setGeometry(
            global_pos.x(),
            global_pos.y(),
            video_rect.width(),
            video_rect.height()
        )
        self.subtitle_window.raise_()

        if hasattr(self, 'subtitle_overlay'):
            self.subtitle_overlay.updateGeometry()
            self.subtitle_overlay.update()
    
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self.update_subtitle_window_geometry()
    
    def moveEvent(self, event):
        """Handle window move - keep subtitle window synchronized"""
        super().moveEvent(event)
        self.update_subtitle_window_geometry()
    
    def closeEvent(self, event):
        """Handle window close with proper cleanup to prevent memory leaks"""
        try:
            # Stop resource monitor timer
            if hasattr(self, 'resource_monitor_timer') and self.resource_monitor_timer.isActive():
                self.resource_monitor_timer.stop()
            
            # Cancel all background tasks
            if hasattr(self, 'task_manager') and self.task_manager:
                active_tasks = self.task_manager.get_active_tasks()
                if active_tasks:
                    reply = QMessageBox.question(
                        self,
                        "Background Tasks Running",
                        f"{len(active_tasks)} background task(s) still running.\nCancel them and exit?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        event.ignore()
                        return
                    
                    # Cancel all tasks
                    for task_id in active_tasks:
                        self.task_manager.cancel_task(task_id)
            
            # Stop all timers
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
            if hasattr(self, 'mouse_move_timer') and self.mouse_move_timer.isActive():
                self.mouse_move_timer.stop()
            
            # Stop and release media player
            if hasattr(self, 'media_player') and self.media_player:
                self.media_player.stop()
                self.media_player.release()
            
            # Release VLC instance
            if hasattr(self, 'instance') and self.instance:
                self.instance.release()
            
            # Stop network casting
            if hasattr(self, 'casting_manager') and self.casting_manager:
                if self.casting_manager.is_casting:
                    self.casting_manager.stop()
                self.casting_manager.cleanup()
            
            # Close subtitle window
            if hasattr(self, 'subtitle_window') and self.subtitle_window:
                self.subtitle_window.close()
                self.subtitle_window.deleteLater()
            
            # Close dialogs
            if hasattr(self, 'subtitle_settings_dialog') and self.subtitle_settings_dialog:
                self.subtitle_settings_dialog.close()
                self.subtitle_settings_dialog.deleteLater()
            
            if hasattr(self, 'streaming_stats_dialog') and self.streaming_stats_dialog:
                self.streaming_stats_dialog.close()
                self.streaming_stats_dialog.deleteLater()
            
            # Clear subtitle cache
            if hasattr(self, 'current_subtitles'):
                self.current_subtitles.clear()
            
            # Remove event filter
            try:
                QApplication.instance().removeEventFilter(self)
            except:
                pass
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
        
        event.accept()


def main():
    """Main entry point for SubtitlePlayer"""
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
