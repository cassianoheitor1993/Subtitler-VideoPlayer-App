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
    QMenu, QMessageBox, QSplitter, QSplitterHandle, QSizePolicy
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
from casting_manager import CastingManager, CastingError, CastingConfig

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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000;")
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events"""
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

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
        
        self.config_manager = ConfigManager()
        self.subtitle_parser = SubtitleParser()
        self.current_video = None
        self.current_subtitles = []
        self.subtitle_style = SubtitleStyle()
        self.subtitle_settings_dialog = None
        self.playback_rate = 1.0
        self._sample_autoplayed = False
        
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
        self.casting_manager = CastingManager(self.instance)
        
        # Timer for updating UI
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        
        self.init_ui()
        self.apply_theme()
        QTimer.singleShot(0, self._autoplay_sample_video)
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("SubtitlePlayer - Professional Video Player")
        self.setGeometry(100, 100, 1200, 700)
        
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
        self.video_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_frame.customContextMenuRequested.connect(self.show_video_context_menu)
        
        # Connect double-click signal
        self.video_frame.double_clicked.connect(self.video_double_click)
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
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        self.cast_status_label = QLabel("")
        self.cast_status_label.setStyleSheet("color: #8cdaff;")
        self.statusBar().addPermanentWidget(self.cast_status_label)
        
        # Connect VLC to video frame - this embeds the video natively
        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))
        
        # Create a separate window for subtitles that stays on top
        self.create_subtitle_window()
    
    def create_control_panel(self):
        """Create video control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMinimumHeight(120)
        
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Timeline
        timeline_layout = QHBoxLayout()
        
        self.time_label = QLabel("00:00:00")
        self.time_label.setMinimumWidth(80)
        timeline_layout.addWidget(self.time_label)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMaximum(1000)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.slider_pressed)
        self.position_slider.sliderReleased.connect(self.slider_released)
        # Enable click-to-seek on timeline
        self.position_slider.mousePressEvent = self.slider_click_seek
        timeline_layout.addWidget(self.position_slider)
        
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setMinimumWidth(80)
        timeline_layout.addWidget(self.duration_label)
        
        layout.addLayout(timeline_layout)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        
        # Open file button
        self.open_btn = QPushButton("Open Video")
        self.open_btn.clicked.connect(self.open_file)
        controls_layout.addWidget(self.open_btn)
        
        # Play/Pause button
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_pause_btn.clicked.connect(self.play_pause)
        self.play_pause_btn.setEnabled(False)
        controls_layout.addWidget(self.play_pause_btn)
        
        # Stop button
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        # Subtitle button
        self.subtitle_btn = QPushButton("Load Subtitles")
        self.subtitle_btn.clicked.connect(self.open_subtitle)
        self.subtitle_btn.setEnabled(False)
        controls_layout.addWidget(self.subtitle_btn)
        
        # Download subtitle button
        self.download_subtitle_btn = QPushButton("Download Subtitles")
        self.download_subtitle_btn.clicked.connect(self.show_subtitle_search)
        self.download_subtitle_btn.setEnabled(False)
        controls_layout.addWidget(self.download_subtitle_btn)
        
        # Subtitle settings sidebar toggle button
        self.toggle_sidebar_btn = QPushButton("⚙ Settings Sidebar")
        self.toggle_sidebar_btn.clicked.connect(self.toggle_subtitle_sidebar)
        controls_layout.addWidget(self.toggle_sidebar_btn)
        
        # Legacy subtitle settings button
        self.legacy_settings_btn = QPushButton("⚙ Legacy Settings")
        self.legacy_settings_btn.clicked.connect(self.show_subtitle_settings)
        controls_layout.addWidget(self.legacy_settings_btn)
        
        controls_layout.addStretch()
        
        # Volume control
        volume_label = QLabel("Volume:")
        controls_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(self.config_manager.config.volume)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel(f"{self.config_manager.config.volume}%")
        self.volume_label.setMinimumWidth(40)
        controls_layout.addWidget(self.volume_label)
        
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

        try:
            self.load_video(str(sample_path), loop=True)
            self._remove_sample_from_recents(str(sample_path))

            if not self.media_player.is_playing():
                self.play_pause()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[Startup] Failed to load sample video: {exc}")
            return

        self.statusBar().showMessage("Sample video ready. Load your own file anytime.", 5000)
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
        """Begin HTTP casting for the auto-loaded sample video."""
        if self.casting_manager.is_casting:
            return

        if not self.current_video:
            return

        media = self.instance.media_new(self.current_video)

        host_ip = self._resolve_host_ip()
        config = CastingConfig(host="0.0.0.0", port=8080)

        try:
            url = self.casting_manager.start_http_stream(media, config, loop=True)
        except CastingError as exc:
            print(f"[Startup] Unable to start sample casting: {exc}")
            return

        resolved_url = url.replace("0.0.0.0", host_ip) if host_ip != "0.0.0.0" else url

        if hasattr(self, "cast_status_label"):
            self.cast_status_label.setText(f"Cast: {resolved_url}")

        try:
            SAMPLE_CAST_URL_FILE.write_text(resolved_url)
            SAMPLE_CAST_LOG_FILE.write_text(f"Sample casting active at {resolved_url}\n")
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[Startup] Warning: could not persist cast URL: {exc}")

        print(f"[Startup] Sample casting ready at {resolved_url}", flush=True)
        self.statusBar().showMessage(f"Sample stream ready at {resolved_url}", 5000)

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
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Video", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        open_subtitle_action = QAction("Load Subtitle File", self)
        open_subtitle_action.setShortcut("Ctrl+S")
        open_subtitle_action.triggered.connect(self.open_subtitle)
        file_menu.addAction(open_subtitle_action)
        
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Playback menu
        playback_menu = menubar.addMenu("Playback")
        
        play_action = QAction("Play/Pause", self)
        play_action.setShortcut("Space")
        play_action.triggered.connect(self.play_pause)
        playback_menu.addAction(play_action)
        
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop)
        playback_menu.addAction(stop_action)
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        playback_menu.addAction(fullscreen_action)
        
        # Subtitles menu
        subtitle_menu = menubar.addMenu("Subtitles")
        
        download_action = QAction("Download Subtitles", self)
        download_action.setShortcut("Ctrl+D")
        download_action.triggered.connect(self.show_subtitle_search)
        subtitle_menu.addAction(download_action)
        
        settings_action = QAction("Subtitle Settings", self)
        settings_action.triggered.connect(self.show_subtitle_settings)
        subtitle_menu.addAction(settings_action)
        
        subtitle_menu.addSeparator()
        
        ai_gen_action = QAction("Generate Subtitles (AI)", self)
        ai_gen_action.setShortcut("Ctrl+G")
        ai_gen_action.triggered.connect(self.show_ai_subtitle_generator)
        subtitle_menu.addAction(ai_gen_action)

        # Cast menu
        cast_menu = menubar.addMenu("Cast")

        start_cast_action = QAction("Start HTTP Cast", self)
        start_cast_action.triggered.connect(self.start_network_cast)
        cast_menu.addAction(start_cast_action)

        stop_cast_action = QAction("Stop Cast", self)
        stop_cast_action.triggered.connect(self.stop_network_cast)
        cast_menu.addAction(stop_cast_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.clear()
        
        for filepath in self.config_manager.recent_files:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                action = QAction(filename, self)
                action.setData(filepath)
                action.triggered.connect(lambda checked, path=filepath: self.load_video(path))
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
    
    def load_video(self, file_path: str, *, loop: bool = False):
        """Load and play video file"""
        self.current_video = file_path

        if self.casting_manager.is_casting:
            self.casting_manager.stop()
            if hasattr(self, "cast_status_label"):
                self.cast_status_label.clear()
            self.statusBar().showMessage("Casting stopped for new video", 3000)
        
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
        self.subtitle_btn.setEnabled(True)
        self.download_subtitle_btn.setEnabled(True)
        
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
        
        self.statusBar().showMessage(f"Playing: {os.path.basename(file_path)}")
    
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
                
                # Update status with subtitle count
                subtitle_count = len(self.current_subtitles)
                self.statusBar().showMessage(
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
        else:
            self.media_player.play()
            self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.timer.start()
    
    def stop(self):
        """Stop playback"""
        self.media_player.stop()
        self.timer.stop()
        self.play_pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.position_slider.setValue(0)
        self.subtitle_overlay.set_subtitle("")
    
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
            # Re-enable menu bar and status bar
            self.menuBar().show()
            self.statusBar().show()
        else:
            self.showFullScreen()
            # Keep menu bar visible in fullscreen for easy exit
            self.menuBar().show()
            self.statusBar().hide()
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # ESC key exits fullscreen
        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.toggle_fullscreen()
        # F key toggles fullscreen
        elif event.key() == Qt.Key.Key_F:
            self.toggle_fullscreen()
        # Space bar plays/pauses
        elif event.key() == Qt.Key.Key_Space:
            self.play_pause()
        else:
            super().keyPressEvent(event)
    
    def video_double_click(self, event):
        """Handle double-click on video frame to toggle fullscreen"""
        self.toggle_fullscreen()
    
    def show_video_context_menu(self, position):
        """Show context menu on right-click"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
        """)
        
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
        
        # Settings shortcuts
        sidebar_action = menu.addAction("🛠 Sidebar Settings")
        sidebar_action.triggered.connect(self.ensure_sidebar_visible)

        legacy_action = menu.addAction("⚙ Legacy Settings Dialog")
        legacy_action.triggered.connect(self.show_subtitle_settings)

        menu.addSeparator()

        # Fullscreen
        if self.isFullScreen():
            fullscreen_action = menu.addAction("⊡ Exit Fullscreen")
        else:
            fullscreen_action = menu.addAction("⛶ Fullscreen")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
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
        faster_action = menu.addAction("⏩ Speed +0.25x")
        faster_action.triggered.connect(lambda: self.adjust_playback_speed(0.25))

        slower_action = menu.addAction("⏪ Speed -0.25x")
        slower_action.triggered.connect(lambda: self.adjust_playback_speed(-0.25))

        reset_speed_action = menu.addAction("⏯ Reset Speed (1.0x)")
        reset_speed_action.triggered.connect(self.reset_playback_speed)

        menu.addSeparator()

        # Casting controls
        if self.casting_manager.is_casting:
            stop_cast_action = menu.addAction("🛑 Stop Network Cast")
            stop_cast_action.triggered.connect(self.stop_network_cast)
            url = self.casting_manager.url or "(unknown)"
            url_action = menu.addAction(f"🔗 {url}")
            url_action.setEnabled(False)
        else:
            start_cast_action = menu.addAction("🛰 Start Network Cast")
            start_cast_action.setEnabled(self.current_video is not None)
            start_cast_action.triggered.connect(self.start_network_cast)

        # Subtitle actions
        load_sub_action = menu.addAction("📄 Load Subtitle File")
        load_sub_action.triggered.connect(self.open_subtitle)
        
        download_sub_action = menu.addAction("⬇ Download Subtitles")
        download_sub_action.triggered.connect(self.show_subtitle_search)
        download_sub_action.setEnabled(self.current_video is not None)
        
        settings_action = menu.addAction("⚙ Subtitle Settings")
        settings_action.triggered.connect(self.show_subtitle_settings)
        
        menu.addSeparator()
        
        # AI Subtitle Generation
        ai_action = menu.addAction("🤖 Generate Subtitles (AI)")
        ai_action.triggered.connect(self.show_ai_subtitle_generator)
        ai_action.setEnabled(self.current_video is not None)
        
        # Show menu at cursor position
        menu.exec(self.video_frame.mapToGlobal(position))

    def ensure_sidebar_visible(self):
        """Ensure the sidebar is visible without toggling off inadvertently"""
        if not self.sidebar_visible:
            self.toggle_subtitle_sidebar()
        else:
            self.sidebar_container.show()
            self.subtitle_sidebar.show()
            self.toggle_sidebar_btn.setText("⬅ Hide Settings")
        self.update_subtitle_window_geometry()

    def adjust_volume(self, delta):
        """Adjust master volume by delta percent"""
        current_volume = self.media_player.audio_get_volume()
        if current_volume == -1:
            current_volume = self.volume_slider.value()
        new_volume = max(0, min(100, current_volume + delta))
        self.volume_slider.setValue(new_volume)
        self.set_volume(new_volume)
        self.statusBar().showMessage(f"Volume set to {new_volume}%", 2000)

    def toggle_mute(self):
        """Toggle audio mute state"""
        muted = self.media_player.audio_get_mute()
        self.media_player.audio_set_mute(not muted)
        self.statusBar().showMessage("Audio muted" if not muted else "Audio unmuted", 2000)

    def adjust_playback_speed(self, delta):
        """Adjust playback speed by delta"""
        new_rate = max(0.25, min(4.0, self.playback_rate + delta))
        if abs(new_rate - self.playback_rate) < 1e-3:
            return
        if self.media_player.set_rate(new_rate) == 0:
            self.playback_rate = new_rate
            self.statusBar().showMessage(f"Playback speed: {self.playback_rate:.2f}x", 2000)
        else:
            self.statusBar().showMessage("Unable to change playback speed", 2000)

    def reset_playback_speed(self):
        """Reset playback speed to normal"""
        if self.media_player.set_rate(1.0) == 0:
            self.playback_rate = 1.0
            self.statusBar().showMessage("Playback speed reset to 1.00x", 2000)

    def start_network_cast(self):
        """Start casting the current media over HTTP."""
        if not self.current_video:
            QMessageBox.information(
                self,
                "No Video",
                "Load a video before starting a casting session."
            )
            return

        if self.casting_manager.is_casting:
            QMessageBox.information(
                self,
                "Casting Already Active",
                f"Streaming is already active at:\n{self.casting_manager.url}"
            )
            return

        media = None
        if self.current_video and os.path.exists(self.current_video):
            media = self.instance.media_new(self.current_video)
        else:
            media = self.media_player.get_media()
            if media is None and self.current_video:
                media = self.instance.media_new(self.current_video)

        try:
            host_ip = self._resolve_host_ip()
            config = CastingConfig(host="0.0.0.0", port=8080)
            url = self.casting_manager.start_http_stream(media, config)
            resolved_url = url.replace("0.0.0.0", host_ip) if host_ip != "0.0.0.0" else url
        except CastingError as exc:
            QMessageBox.critical(
                self,
                "Casting Failed",
                f"Unable to start network casting.\n\n{exc}"
            )
            return

        if hasattr(self, "cast_status_label"):
            self.cast_status_label.setText(f"Cast: {resolved_url}")
        self.statusBar().showMessage(f"Casting started: {resolved_url}", 5000)
        QMessageBox.information(
            self,
            "Casting Started",
            "Streaming started successfully.\n\n"
            f"Access it from another device using this URL:\n{resolved_url}"
        )

    def stop_network_cast(self):
        """Stop the active casting session."""
        if not self.casting_manager.is_casting:
            self.statusBar().showMessage("No active casting session", 2000)
            return

        self.casting_manager.stop()
        if hasattr(self, "cast_status_label"):
            self.cast_status_label.clear()
        self.statusBar().showMessage("Casting stopped", 3000)
        QMessageBox.information(
            self,
            "Casting Stopped",
            "Network casting has been stopped."
        )
    
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
            self.toggle_sidebar_btn.setText("⬅ Hide Settings")
            if self.subtitle_settings_dialog and self.subtitle_settings_dialog.isVisible():
                self.subtitle_settings_dialog.reject()
        else:
            self.sidebar_container.hide()
            self.subtitle_sidebar.hide()
            self.splitter.setSizes([self.width(), 0])
            self.toggle_sidebar_btn.setText("⚙ Settings Sidebar")
        self.update_subtitle_window_geometry()
    
    def on_sidebar_settings_changed(self, style):
        """Handle changes from subtitle settings sidebar"""
        self.subtitle_style = style
        self.subtitle_overlay.set_style(self.subtitle_style)
    
    def show_subtitle_settings(self):
        """Show subtitle settings dialog"""
        # Import here to avoid circular dependency
        from subtitle_settings_dialog import SubtitleSettingsDialog
        
        if self.sidebar_visible:
            self.sidebar_visible = False
            self.sidebar_container.hide()
            self.subtitle_sidebar.hide()
            self.splitter.setSizes([self.width(), 0])
            self.toggle_sidebar_btn.setText("⚙ Settings Sidebar")

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
        dialog.toggle_sidebar_requested.connect(self.toggle_subtitle_sidebar)
        self.subtitle_settings_dialog = dialog

        try:
            if dialog.exec():
                self.subtitle_style = dialog.get_style()
                self.subtitle_overlay.set_style(self.subtitle_style)
            
                # Re-apply timing offset
                if self.current_subtitles:
                    base_subtitles = self.subtitle_parser.parse_file(
                        self.config_manager.get_subtitle_file_for_video(self.current_video)
                    )
                    self.current_subtitles = self.subtitle_parser.adjust_timing(
                        base_subtitles,
                        self.subtitle_style.timing_offset
                    )
                
                # Save style
                if self.current_video:
                    self.config_manager.save_subtitle_style(self.subtitle_style, self.current_video)
        finally:
            self._clear_subtitle_dialog_reference()
    
    def show_ai_subtitle_generator(self):
        """Show AI subtitle generation dialog"""
        if not self.current_video:
            QMessageBox.information(self, "No Video", "Please load a video first")
            return
        
        try:
            from ai_subtitle_dialog import AISubtitleDialog
            from ai_subtitle_generator import AISubtitleGenerator
            
            dialog = AISubtitleDialog(self.current_video, self)
            if dialog.exec():
                segments = dialog.get_generated_segments()
                if segments:
                    # Save to SRT file
                    subtitle_path = dialog.get_subtitle_path()
                    generator = AISubtitleGenerator()
                    if generator.save_to_srt(segments, subtitle_path):
                        # Load the generated subtitle
                        self.load_subtitle(subtitle_path)
                        QMessageBox.information(
                            self,
                            "Success",
                            f"AI-generated subtitles saved and loaded!\n{subtitle_path}"
                        )
        except ImportError as e:
            QMessageBox.warning(
                self,
                "Dependencies Missing",
                "AI subtitle generation requires additional dependencies.\n\n"
                "Install with:\n"
                "pip install openai-whisper torch\n\n"
                "See Subtitles > Generate Subtitles (AI) for details."
            )
    
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
        """Handle window close"""
        self.media_player.stop()
        self.timer.stop()
        # Close subtitle window if it exists
        if hasattr(self, 'subtitle_window'):
            self.subtitle_window.close()
        if hasattr(self, 'casting_manager'):
            self.casting_manager.cleanup()
        event.accept()


def main():
    """Main entry point for SubtitlePlayer"""
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
