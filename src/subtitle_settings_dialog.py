"""
Subtitle Settings Dialog
Configure subtitle appearance and timing
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QDoubleSpinBox, QComboBox, QGroupBox, QCheckBox,
    QColorDialog, QFontComboBox, QGridLayout, QScrollArea, QWidget,
    QSizePolicy, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QResizeEvent

from config_manager import SubtitleStyle


class ColorButton(QPushButton):
    """Button for selecting colors"""
    
    def __init__(self, initial_color="#FFFFFF"):
        super().__init__()
        self.color = QColor(initial_color)
        self.setFixedWidth(60)
        self.update_style()
        self.clicked.connect(self.select_color)
    
    def update_style(self):
        """Update button style with current color"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: 2px solid #3d3d3d;
                border-radius: 4px;
            }}
        """)
    
    def select_color(self):
        """Open color picker"""
        color = QColorDialog.getColor(self.color, self, "Select Color")
        if color.isValid():
            self.color = color
            self.update_style()
    
    def get_color(self):
        """Get color as hex string"""
        return self.color.name()
    
    def set_color(self, color_str):
        """Set color from string"""
        self.color = QColor(color_str)
        self.update_style()


class SubtitleSettingsDialog(QDialog):
    """Dialog for configuring subtitle appearance"""
    toggle_sidebar_requested = pyqtSignal()
    translation_started = pyqtSignal(str)
    translation_progress = pyqtSignal(str, int)
    translation_finished = pyqtSignal(str, bool)
    
    def __init__(self, current_style: SubtitleStyle, parent=None, subtitles=None, current_time_func=None, video_path=None, subtitle_path=None):
        super().__init__(parent)
        self.current_style = current_style
        self.subtitles = subtitles or []
        self.current_time_func = current_time_func
        self.video_path = video_path
        self.subtitle_path = subtitle_path
        self.translation_cancelled = False  # Flag to track translation cancellation
        self._translation_running = False
        self._close_after_translation = False
        self.init_ui()
        self.load_settings()
    
    def switch_to_sidebar(self):
        """Close dialog and request sidebar view"""
        self.toggle_sidebar_requested.emit()
        self.reject()

    def closeEvent(self, event):
        """Prevent closing while translation is still running."""
        if self._translation_running:
            if not self.translation_cancelled:
                reply = QMessageBox.question(
                    self,
                    "Cancel Translation?",
                    "A translation is still running.\n\n"
                    "Do you want to cancel it and close the dialog?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._close_after_translation = True
                    self.cancel_translation()
                    self.hide()
                event.ignore()
                return

            # Already cancelling; wait for completion before closing
            self.hide()
            event.ignore()
            return

        self._close_after_translation = False
        super().closeEvent(event)

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Subtitle Settings")
        self.setModal(True)
        self.resize(900, 600)  # Wider default, less tall
        self.setMinimumSize(700, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Header with toggle button
        header_layout = QHBoxLayout()
        header_title = QLabel("Legacy Subtitle Settings")
        header_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        self.sidebar_toggle_btn = QPushButton("Sidebar View")
        self.sidebar_toggle_btn.setObjectName("SidebarToggleButton")
        self.sidebar_toggle_btn.clicked.connect(self.switch_to_sidebar)
        header_layout.addWidget(self.sidebar_toggle_btn)
        main_layout.addLayout(header_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        self.content_layout = QGridLayout()
        self.content_layout.setSpacing(10)
        content_widget.setLayout(self.content_layout)
        scroll.setWidget(content_widget)
        
        main_layout.addWidget(scroll)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        # Font family
        family_layout = QHBoxLayout()
        family_label = QLabel("Font Family:")
        self.font_family = QFontComboBox()
        family_layout.addWidget(family_label)
        family_layout.addWidget(self.font_family)
        font_layout.addLayout(family_layout)
        
        # Font size
        size_layout = QHBoxLayout()
        size_label = QLabel("Font Size:")
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 100)
        self.font_size.setSuffix(" pt")
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.font_size)
        size_layout.addStretch()
        font_layout.addLayout(size_layout)
        
        # Font style
        style_layout = QHBoxLayout()
        self.font_bold = QCheckBox("Bold")
        self.font_italic = QCheckBox("Italic")
        style_layout.addWidget(self.font_bold)
        style_layout.addWidget(self.font_italic)
        style_layout.addStretch()
        font_layout.addLayout(style_layout)
        
        font_group.setLayout(font_layout)
        
        # Color settings
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout()
        
        # Text color
        text_color_layout = QHBoxLayout()
        text_color_label = QLabel("Text Color:")
        self.text_color_btn = ColorButton()
        text_color_layout.addWidget(text_color_label)
        text_color_layout.addWidget(self.text_color_btn)
        text_color_layout.addStretch()
        color_layout.addLayout(text_color_layout)
        
        # Stroke color
        stroke_color_layout = QHBoxLayout()
        stroke_color_label = QLabel("Stroke Color:")
        self.stroke_color_btn = ColorButton("#000000")
        stroke_color_layout.addWidget(stroke_color_label)
        stroke_color_layout.addWidget(self.stroke_color_btn)
        stroke_color_layout.addStretch()
        color_layout.addLayout(stroke_color_layout)
        
        # Stroke width
        stroke_width_layout = QHBoxLayout()
        stroke_width_label = QLabel("Stroke Width:")
        self.stroke_width = QSpinBox()
        self.stroke_width.setRange(0, 10)
        self.stroke_width.setSuffix(" px")
        stroke_width_layout.addWidget(stroke_width_label)
        stroke_width_layout.addWidget(self.stroke_width)
        stroke_width_layout.addStretch()
        color_layout.addLayout(stroke_width_layout)
        
        # Background color
        bg_color_layout = QHBoxLayout()
        bg_color_label = QLabel("Background Color:")
        self.bg_color_btn = ColorButton("rgba(0, 0, 0, 180)")
        self.bg_enabled = QCheckBox("Enabled")
        self.bg_enabled.setChecked(True)
        bg_color_layout.addWidget(bg_color_label)
        bg_color_layout.addWidget(self.bg_color_btn)
        bg_color_layout.addWidget(self.bg_enabled)
        bg_color_layout.addStretch()
        color_layout.addLayout(bg_color_layout)
        
        color_group.setLayout(color_layout)
        
        # Position settings
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout()
        
        # Vertical position
        v_pos_layout = QHBoxLayout()
        v_pos_label = QLabel("Vertical Position:")
        self.v_position = QComboBox()
        self.v_position.addItems(["Top", "Center", "Bottom"])
        v_pos_layout.addWidget(v_pos_label)
        v_pos_layout.addWidget(self.v_position)
        v_pos_layout.addStretch()
        position_layout.addLayout(v_pos_layout)
        
        # Horizontal position
        h_pos_layout = QHBoxLayout()
        h_pos_label = QLabel("Horizontal Position:")
        self.h_position = QComboBox()
        self.h_position.addItems(["Left", "Center", "Right"])
        h_pos_layout.addWidget(h_pos_label)
        h_pos_layout.addWidget(self.h_position)
        h_pos_layout.addStretch()
        position_layout.addLayout(h_pos_layout)
        
        # Vertical margin
        v_margin_layout = QHBoxLayout()
        v_margin_label = QLabel("Vertical Margin:")
        self.v_margin = QSpinBox()
        self.v_margin.setRange(0, 300)
        self.v_margin.setSuffix(" px")
        v_margin_layout.addWidget(v_margin_label)
        v_margin_layout.addWidget(self.v_margin)
        v_margin_layout.addStretch()
        position_layout.addLayout(v_margin_layout)
        
        # Horizontal margin
        h_margin_layout = QHBoxLayout()
        h_margin_label = QLabel("Horizontal Margin:")
        self.h_margin = QSpinBox()
        self.h_margin.setRange(0, 300)
        self.h_margin.setSuffix(" px")
        h_margin_layout.addWidget(h_margin_label)
        h_margin_layout.addWidget(self.h_margin)
        h_margin_layout.addStretch()
        position_layout.addLayout(h_margin_layout)
        
        position_group.setLayout(position_layout)
        
        # Timing settings
        timing_group = QGroupBox("Timing Synchronization")
        timing_layout = QVBoxLayout()
        
        timing_info = QLabel("Adjust subtitle timing if out of sync with video")
        timing_info.setWordWrap(True)
        timing_layout.addWidget(timing_info)
        
        offset_layout = QHBoxLayout()
        offset_label = QLabel("Time Offset:")
        self.timing_offset = QDoubleSpinBox()
        self.timing_offset.setRange(-60.0, 60.0)
        self.timing_offset.setSingleStep(0.1)
        self.timing_offset.setSuffix(" sec")
        self.timing_offset.setDecimals(1)
        self.timing_offset.valueChanged.connect(self.update_timing_preview)
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.timing_offset)
        offset_layout.addStretch()
        timing_layout.addLayout(offset_layout)
        
        # Timing preview
        self.timing_preview_label = QLabel("Current subtitle at this time:")
        timing_layout.addWidget(self.timing_preview_label)
        
        self.timing_preview_text = QLabel("Play video to see subtitle preview")
        self.timing_preview_text.setWordWrap(True)
        self.timing_preview_text.setStyleSheet("""
            QLabel {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
                border-radius: 4px;
                padding: 10px;
                min-height: 40px;
            }
        """)
        timing_layout.addWidget(self.timing_preview_text)
        
        timing_group.setLayout(timing_layout)
        
        # Translation feature
        translation_group = QGroupBox("Subtitle Translation")
        translation_layout = QVBoxLayout()
        
        trans_info = QLabel("Translate subtitles to another language using AI")
        trans_info.setWordWrap(True)
        translation_layout.addWidget(trans_info)
        
        trans_select_layout = QHBoxLayout()
        trans_label = QLabel("Target Language:")
        self.translation_combo = QComboBox()
        self.translation_combo.addItems([
            "No Translation",
            "English (US)",
            "English (UK)", 
            "English (Canada)",
            "Portuguese (Brazil)",
            "Portuguese (Portugal)",
            "Spanish (Spain)",
            "Spanish (Latin America)",
            "Chinese (Simplified)",
            "Chinese (Traditional)",
            "French",
            "German",
            "Italian",
            "Japanese",
            "Korean",
            "Russian",
            "Arabic",
            "Hindi"
        ])
        trans_select_layout.addWidget(trans_label)
        trans_select_layout.addWidget(self.translation_combo)
        trans_select_layout.addStretch()
        translation_layout.addLayout(trans_select_layout)
        
        # Translation buttons layout
        trans_buttons_layout = QHBoxLayout()
        
        self.translate_btn = QPushButton("🌐 Translate Subtitles")
        self.translate_btn.clicked.connect(self.translate_subtitles)
        trans_buttons_layout.addWidget(self.translate_btn)
        
        self.cancel_translation_btn = QPushButton("❌ Cancel")
        self.cancel_translation_btn.clicked.connect(self.cancel_translation)
        self.cancel_translation_btn.setVisible(False)
        self.cancel_translation_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        trans_buttons_layout.addWidget(self.cancel_translation_btn)
        
        trans_buttons_layout.addStretch()
        translation_layout.addLayout(trans_buttons_layout)
        
        # Progress bar for translation
        self.translation_progress_bar = QProgressBar()
        self.translation_progress_bar.setVisible(False)
        self.translation_progress_bar.setMinimum(0)
        self.translation_progress_bar.setMaximum(100)
        self.translation_progress_bar.setTextVisible(True)
        self.translation_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        translation_layout.addWidget(self.translation_progress_bar)
        
        self.translation_status = QLabel("")
        self.translation_status.setWordWrap(True)
        translation_layout.addWidget(self.translation_status)
        
        translation_group.setLayout(translation_layout)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("This is a sample subtitle")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(80)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                color: white;
                padding: 10px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        
        # Store references to group widgets for responsive layout
        self._group_widgets = {
            'font': font_group,
            'color': color_group,
            'position': position_group,
            'timing': timing_group,
            'translation': translation_group,
            'preview': preview_group
        }
        
        # Add groups to grid layout - responsive arrangement
        # Initially in 2 columns, will rearrange on resize
        self.content_layout.addWidget(font_group, 0, 0)
        self.content_layout.addWidget(color_group, 0, 1)
        self.content_layout.addWidget(position_group, 1, 0)
        self.content_layout.addWidget(timing_group, 1, 1)
        self.content_layout.addWidget(translation_group, 2, 0)
        self.content_layout.addWidget(preview_group, 2, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.apply_btn)
        
        main_layout.addLayout(button_layout)
        
        # Connect signals for live preview
        self.font_family.currentFontChanged.connect(self.update_preview)
        self.font_size.valueChanged.connect(self.update_preview)
        self.font_bold.stateChanged.connect(self.update_preview)
        self.font_italic.stateChanged.connect(self.update_preview)
        self.text_color_btn.clicked.connect(self.update_preview)
        
        self.apply_style()
    
    def apply_style(self):
        """Apply styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QGroupBox {
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #cccccc;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 4px;
            }
            QCheckBox {
                color: #cccccc;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#SidebarToggleButton {
                background-color: transparent;
                color: #9ec0ff;
                border: 1px solid #1f4a8c;
                padding: 6px 14px;
            }
            QPushButton#SidebarToggleButton:hover {
                background-color: rgba(30, 90, 160, 0.35);
            }
        """)
    
    def load_settings(self):
        """Load current settings into UI"""
        # Set font family by creating QFont object from string
        font = QFont(self.current_style.font_family)
        self.font_family.setCurrentFont(font)
        self.font_size.setValue(self.current_style.font_size)
        self.font_bold.setChecked(self.current_style.font_bold)
        self.font_italic.setChecked(self.current_style.font_italic)
        
        self.text_color_btn.set_color(self.current_style.text_color)
        self.stroke_color_btn.set_color(self.current_style.stroke_color)
        self.stroke_width.setValue(self.current_style.stroke_width)
        
        if self.current_style.background_color:
            self.bg_color_btn.set_color(self.current_style.background_color)
            self.bg_enabled.setChecked(True)
        else:
            self.bg_enabled.setChecked(False)
        
        self.v_position.setCurrentText(self.current_style.position_vertical.capitalize())
        self.h_position.setCurrentText(self.current_style.position_horizontal.capitalize())
        self.v_margin.setValue(self.current_style.margin_vertical)
        self.h_margin.setValue(self.current_style.margin_horizontal)
        
        self.timing_offset.setValue(self.current_style.timing_offset)
        
        self.update_preview()
    
    def get_style(self) -> SubtitleStyle:
        """Get style from UI settings"""
        return SubtitleStyle(
            font_family=self.font_family.currentFont().family(),
            font_size=self.font_size.value(),
            font_bold=self.font_bold.isChecked(),
            font_italic=self.font_italic.isChecked(),
            text_color=self.text_color_btn.get_color(),
            stroke_color=self.stroke_color_btn.get_color(),
            stroke_width=self.stroke_width.value(),
            background_color=self.bg_color_btn.get_color() if self.bg_enabled.isChecked() else "",
            position_vertical=self.v_position.currentText().lower(),
            position_horizontal=self.h_position.currentText().lower(),
            margin_vertical=self.v_margin.value(),
            margin_horizontal=self.h_margin.value(),
            timing_offset=self.timing_offset.value()
        )
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.current_style = SubtitleStyle()
        self.load_settings()
    
    def update_preview(self):
        """Update subtitle preview"""
        style = self.get_style()
        
        font_style = ""
        if style.font_bold:
            font_style += "font-weight: bold; "
        if style.font_italic:
            font_style += "font-style: italic; "
        
        bg = style.background_color if style.background_color else "transparent"
        
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: #000000;
                color: {style.text_color};
                font-family: {style.font_family};
                font-size: {style.font_size}pt;
                {font_style}
                padding: 10px;
            }}
        """)
    
    def update_timing_preview(self):
        """Update timing preview to show which subtitle is at current time"""
        if not self.subtitles or not self.current_time_func:
            self.timing_preview_text.setText("Play video to see subtitle preview")
            return
        
        # Get current time and apply offset
        current_time = self.current_time_func() + self.timing_offset.value()
        
        # Find subtitle at this time
        for subtitle in self.subtitles:
            if subtitle.start_time <= current_time <= subtitle.end_time:
                time_str = self._format_time(current_time)
                self.timing_preview_text.setText(f"[{time_str}] {subtitle.text}")
                self.timing_preview_label.setText(f"✓ Subtitle at {time_str}:")
                return
        
        # No subtitle at this time
        time_str = self._format_time(current_time)
        self.timing_preview_text.setText(f"[{time_str}] (no subtitle)")
        self.timing_preview_label.setText(f"Time {time_str}:")
    
    def _format_time(self, seconds):
        """Format seconds to MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def cancel_translation(self):
        """Cancel ongoing translation"""
        self.translation_cancelled = True
        self.translation_status.setText("⚠️ Cancelling translation...")
        self.cancel_translation_btn.setEnabled(False)
    
    def translate_subtitles(self):
        """Translate subtitles to selected language and save to new file"""
        import os
        from PyQt6.QtWidgets import QMessageBox
        
        if not self.subtitles:
            QMessageBox.warning(
                self,
                "No Subtitles",
                "No subtitles loaded to translate."
            )
            return
        
        target_lang = self.translation_combo.currentText()
        if target_lang == "No Translation":
            self.translation_status.setText("Please select a target language")
            return
        
        if not self.subtitle_path:
            QMessageBox.warning(
                self,
                "No Subtitle File",
                "Cannot translate: no subtitle file is currently loaded."
            )
            return
        
        # Check if translation module is available
        try:
            from subtitle_translator import SubtitleTranslator
        except ImportError:
            QMessageBox.information(
                self,
                "Translation Feature",
                "Subtitle translation requires additional dependencies:\n\n"
                "pip install googletrans==4.0.0rc1\n"
                "# OR\n"
                "pip install deep-translator\n\n"
                "After installation, restart SubtitlePlayer."
            )
            return
        
        # Generate output filename
        base_name = os.path.splitext(self.subtitle_path)[0]
        extension = os.path.splitext(self.subtitle_path)[1]
        
        # Create language code for filename (e.g., "en-US", "pt-BR")
        lang_codes = {
            "English (US)": "en-US",
            "English (UK)": "en-UK",
            "English (Canada)": "en-CA",
            "Portuguese (Brazil)": "pt-BR",
            "Portuguese (Portugal)": "pt-PT",
            "Spanish (Spain)": "es-ES",
            "Spanish (Latin America)": "es-LA",
            "Chinese (Simplified)": "zh-CN",
            "Chinese (Traditional)": "zh-TW",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Japanese": "ja",
            "Korean": "ko",
            "Russian": "ru",
            "Arabic": "ar",
            "Hindi": "hi"
        }
        
        lang_code = lang_codes.get(target_lang, "translated")
        output_path = f"{base_name}.{lang_code}{extension}"
        
        # Check if file already exists
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"Translated file already exists:\n{os.path.basename(output_path)}\n\n"
                "Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.translation_status.setText("Translation cancelled")
                return
        
        # Reset cancellation flag and show UI
        self.translation_cancelled = False
        self._translation_running = True
        self._close_after_translation = False
        self.translation_status.setText(f"🔄 Translating to {target_lang}...")
        self.translation_progress_bar.setValue(0)
        self.translation_progress_bar.setVisible(True)
        self.translate_btn.setEnabled(False)
        self.cancel_translation_btn.setVisible(True)
        self.cancel_translation_btn.setEnabled(True)
        self.translation_started.emit(target_lang)
        
        # Progress callback to update both status and progress bar
        def update_progress(msg, pct):
            self.translation_status.setText(f"{msg}")
            self.translation_progress_bar.setValue(int(pct))
            # Process events to keep UI responsive
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            self.translation_progress.emit(msg, int(pct))
        
        # Cancel check callback
        def check_cancelled():
            return self.translation_cancelled
        
        try:
            translator = SubtitleTranslator()
            translated_subs = translator.translate_subtitles(
                self.subtitles,
                target_lang,
                update_progress,
                check_cancelled
            )
            
            # Normalize subtitles list for subsequent checks
            translated_subs = translated_subs or []

            # Check if translation was cancelled
            if self.translation_cancelled:
                completed = len(translated_subs)
                total = len(self.subtitles)
                cancel_message = f"❌ Translation cancelled ({completed}/{total} completed)"
                self.translation_status.setText(cancel_message)
                self.translation_progress_bar.setVisible(False)
                self.translate_btn.setEnabled(True)
                self.cancel_translation_btn.setVisible(False)
                
                # Ask if user wants to save partial results
                if translated_subs:
                    reply = QMessageBox.question(
                        self,
                        "Save Partial Translation?",
                        f"Translation was cancelled.\n\n"
                        f"Translated {len(translated_subs)} out of {len(self.subtitles)} subtitles.\n\n"
                        "Would you like to save the partial translation?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        self.translation_finished.emit(cancel_message, False)
                        return
                else:
                    self.translation_finished.emit(cancel_message, False)
                    return
            
            if not translated_subs:
                self.translation_status.setText("❌ Translation failed")
                self.translation_progress_bar.setVisible(False)
                self.translate_btn.setEnabled(True)
                self.cancel_translation_btn.setVisible(False)
                self.translation_finished.emit("❌ Translation failed", False)
                return
            
            # Save translated subtitles to file
            from subtitle_parser import SubtitleParser
            parser = SubtitleParser()
            
            # Determine format from extension
            if extension.lower() == '.srt':
                content = parser.write_srt(translated_subs)
            elif extension.lower() == '.vtt':
                content = parser.write_vtt(translated_subs)
            elif extension.lower() in ['.ass', '.ssa']:
                content = parser.write_ass(translated_subs)
            else:
                # Default to SRT
                content = parser.write_srt(translated_subs)
                output_path = f"{base_name}.{lang_code}.srt"
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Success message with option to load
            self.translation_progress_bar.setValue(100)
            self.translation_status.setText(
                f"✓ Saved: {os.path.basename(output_path)}"
            )
            result_message = f"✓ Saved: {os.path.basename(output_path)}"
            self.translation_finished.emit(result_message, True)
            
            # Hide progress bar and cancel button after a short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.translation_progress_bar.setVisible(False))
            self.cancel_translation_btn.setVisible(False)
            
            reply = QMessageBox.question(
                self,
                "Translation Complete",
                f"Successfully translated {len(translated_subs)} subtitles to {target_lang}!\n\n"
                f"Saved as: {os.path.basename(output_path)}\n\n"
                "Would you like to load the translated subtitles now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Signal to parent to load the new subtitle file
                if self.parent():
                    self.parent().load_subtitle(output_path)
                self.accept()  # Close dialog
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.translation_status.setText(f"❌ Error: {str(e)}")
            self.translation_progress_bar.setVisible(False)
            QMessageBox.critical(
                self,
                "Translation Error",
                f"An error occurred during translation:\n\n{str(e)}\n\n"
                "Check the console for details."
            )
            print(f"Translation error details:\n{error_details}")
            self.translation_finished.emit(f"❌ Error: {str(e)}", False)
        finally:
            self._translation_running = False
            self.translate_btn.setEnabled(True)
            self.cancel_translation_btn.setVisible(False)
            if self._close_after_translation:
                self._close_after_translation = False
                self.close()
    
    def resizeEvent(self, event: QResizeEvent):
        """Handle window resize to rearrange grid layout responsively"""
        super().resizeEvent(event)
        self.rearrange_layout()
    
    def rearrange_layout(self):
        """Rearrange grid layout based on available width"""
        width = self.width()
        
        # Store all group widgets
        if not hasattr(self, '_group_widgets'):
            return
        
        font_group = self._group_widgets.get('font')
        color_group = self._group_widgets.get('color')
        position_group = self._group_widgets.get('position')
        timing_group = self._group_widgets.get('timing')
        translation_group = self._group_widgets.get('translation')
        preview_group = self._group_widgets.get('preview')
        
        if not all([font_group, color_group, position_group, timing_group, translation_group, preview_group]):
            return
        
        # Remove all widgets from grid
        for i in reversed(range(self.content_layout.count())):
            self.content_layout.itemAt(i).widget().setParent(None)
        
        # Determine number of columns based on width
        if width >= 1200:
            # Wide layout: 3 columns
            self.content_layout.addWidget(font_group, 0, 0)
            self.content_layout.addWidget(color_group, 0, 1)
            self.content_layout.addWidget(position_group, 0, 2)
            self.content_layout.addWidget(timing_group, 1, 0)
            self.content_layout.addWidget(translation_group, 1, 1)
            self.content_layout.addWidget(preview_group, 1, 2)
        elif width >= 900:
            # Medium layout: 2 columns
            self.content_layout.addWidget(font_group, 0, 0)
            self.content_layout.addWidget(color_group, 0, 1)
            self.content_layout.addWidget(position_group, 1, 0)
            self.content_layout.addWidget(timing_group, 1, 1)
            self.content_layout.addWidget(translation_group, 2, 0)
            self.content_layout.addWidget(preview_group, 2, 1)
        else:
            # Narrow layout: 1 column
            self.content_layout.addWidget(font_group, 0, 0)
            self.content_layout.addWidget(color_group, 1, 0)
            self.content_layout.addWidget(position_group, 2, 0)
            self.content_layout.addWidget(timing_group, 3, 0)
            self.content_layout.addWidget(translation_group, 4, 0)
            self.content_layout.addWidget(preview_group, 5, 0)
