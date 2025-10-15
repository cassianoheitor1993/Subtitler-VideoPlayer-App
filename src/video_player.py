"""
Main Video Player Window
Professional video player with VLC backend and subtitle support
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QFileDialog, QFrame, QStyle, QApplication,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QPalette, QColor, QFont, QPainter, QPen
import vlc

# Suppress VLC warnings and debug messages
os.environ['VLC_VERBOSE'] = '-1'
import warnings
warnings.filterwarnings('ignore')

from subtitle_parser import SubtitleParser, SubtitleEntry
from config_manager import ConfigManager, SubtitleStyle


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
        max_width = max(metrics.horizontalAdvance(line) for line in lines)
        total_height = line_height * len(lines)
        
        # Calculate position
        x = 0
        if self.style.position_horizontal == 'center':
            x = (self.width() - max_width) // 2
        elif self.style.position_horizontal == 'left':
            x = self.style.margin_horizontal
        else:  # right
            x = self.width() - max_width - self.style.margin_horizontal
        
        if self.style.position_vertical == 'bottom':
            y = self.height() - total_height - self.style.margin_vertical
        elif self.style.position_vertical == 'top':
            y = self.style.margin_vertical
        else:  # center
            y = (self.height() - total_height) // 2
        
        # Draw background
        if self.style.background_color:
            bg_color = QColor(self.style.background_color)
            painter.fillRect(
                x - 10, y - 5,
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
                painter.drawText(x, line_y, line)
        
        # Draw text
        painter.setPen(QColor(self.style.text_color))
        for i, line in enumerate(lines):
            line_y = y + (i + 1) * line_height
            painter.drawText(x, line_y, line)


class VideoPlayer(QMainWindow):
    """Main video player window"""
    
    def __init__(self):
        super().__init__()
        
        self.config_manager = ConfigManager()
        self.subtitle_parser = SubtitleParser()
        self.current_video = None
        self.current_subtitles = []
        self.subtitle_style = SubtitleStyle()
        
        # VLC setup with suppressed logging
        vlc_args = [
            '--no-xlib',
            '--quiet',
            '--no-video-title-show',
            '--avcodec-hw=none',  # Disable hardware acceleration to avoid errors
        ]
        self.instance = vlc.Instance(vlc_args)
        self.media_player = self.instance.media_player_new()
        
        # Timer for updating UI
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)
        
        self.init_ui()
        self.apply_theme()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("SubtitlePlayer - Professional Video Player")
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        central_widget.setLayout(layout)
        
        # Video frame with subtitle overlay
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000;")
        self.video_frame.setMinimumHeight(400)
        self.video_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_frame.customContextMenuRequested.connect(self.show_video_context_menu)
        
        # Enable mouse tracking for double-click
        self.video_frame.mouseDoubleClickEvent = self.video_double_click
        
        # Create stacked layout for video and subtitles
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_frame.setLayout(video_layout)
        
        # Subtitle overlay
        self.subtitle_overlay = SubtitleOverlay(self.video_frame)
        self.subtitle_overlay.setGeometry(0, 0, 1200, 600)
        
        layout.addWidget(self.video_frame, stretch=1)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Connect VLC to video frame
        if sys.platform.startswith('linux'):
            self.media_player.set_xwindow(int(self.video_frame.winId()))
        elif sys.platform == "win32":
            self.media_player.set_hwnd(int(self.video_frame.winId()))
        elif sys.platform == "darwin":
            self.media_player.set_nsobject(int(self.video_frame.winId()))
    
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
        
        # Subtitle settings button
        self.subtitle_settings_btn = QPushButton("Subtitle Settings")
        self.subtitle_settings_btn.clicked.connect(self.show_subtitle_settings)
        controls_layout.addWidget(self.subtitle_settings_btn)
        
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
    
    def load_video(self, file_path: str):
        """Load and play video file"""
        self.current_video = file_path
        
        # Add to recent files
        self.config_manager.add_recent_file(file_path)
        self.update_recent_menu()
        
        # Load video
        media = self.instance.media_new(file_path)
        self.media_player.set_media(media)
        
        # Enable controls
        self.play_pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.subtitle_btn.setEnabled(True)
        self.download_subtitle_btn.setEnabled(True)
        
        # Try to auto-load subtitle
        subtitle_file = self.config_manager.get_subtitle_file_for_video(file_path)
        if subtitle_file and os.path.exists(subtitle_file):
            self.load_subtitle(subtitle_file)
        else:
            # Check for subtitle file in same directory
            video_path = Path(file_path)
            for ext in ['.srt', '.vtt', '.ass', '.ssa']:
                sub_path = video_path.with_suffix(ext)
                if sub_path.exists():
                    self.load_subtitle(str(sub_path))
                    break
        
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
        self.current_subtitles = self.subtitle_parser.parse_file(file_path)
        
        if self.current_subtitles:
            # Apply timing offset if set
            if self.subtitle_style.timing_offset != 0:
                self.current_subtitles = self.subtitle_parser.adjust_timing(
                    self.current_subtitles,
                    self.subtitle_style.timing_offset
                )
            
            # Save association
            if self.current_video:
                self.config_manager.set_subtitle_file_for_video(self.current_video, file_path)
            
            self.statusBar().showMessage(f"Loaded subtitles: {os.path.basename(file_path)}")
        else:
            QMessageBox.warning(self, "Error", "Could not parse subtitle file")
    
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
        
        # Update time labels
        current_time = self.media_player.get_time() // 1000  # milliseconds to seconds
        duration = self.media_player.get_length() // 1000
        
        self.time_label.setText(self.format_time(current_time))
        self.duration_label.setText(self.format_time(duration))
        
        # Update subtitles
        if self.current_subtitles:
            subtitle_text = self.subtitle_parser.get_subtitle_at_time(
                self.current_subtitles,
                current_time / 1000.0  # Convert to seconds with decimal
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
        
        # Fullscreen
        if self.isFullScreen():
            fullscreen_action = menu.addAction("⊡ Exit Fullscreen")
        else:
            fullscreen_action = menu.addAction("⛶ Fullscreen")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        
        menu.addSeparator()
        
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
    
    def show_subtitle_settings(self):
        """Show subtitle settings dialog"""
        # Import here to avoid circular dependency
        from subtitle_settings_dialog import SubtitleSettingsDialog
        
        dialog = SubtitleSettingsDialog(self.subtitle_style, self)
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
    
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Resize subtitle overlay to match video frame
        self.subtitle_overlay.setGeometry(self.video_frame.rect())
    
    def closeEvent(self, event):
        """Handle window close"""
        self.media_player.stop()
        self.timer.stop()
        event.accept()


def main():
    """Main entry point for SubtitlePlayer"""
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
