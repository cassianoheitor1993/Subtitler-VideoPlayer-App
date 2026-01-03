"""
Professional Sidebar for Subtitle Settings
Allows real-time subtitle customization while watching video
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QColorDialog, QScrollArea,
    QFrame, QGroupBox, QSizePolicy, QDoubleSpinBox, QFontComboBox, QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QIcon
from .config_manager import SubtitleStyle


class SubtitleSettingsSidebar(QWidget):
    """Professional sidebar for subtitle settings"""
    
    settings_changed = pyqtSignal(object)  # Emits SubtitleStyle
    toggle_legacy = pyqtSignal()
    
    def __init__(self, style: SubtitleStyle, parent=None):
        super().__init__(parent)
        self.style = style
        self.setMaximumWidth(480)
        self.setMinimumWidth(260)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.setup_ui()
    
    def setup_ui(self):
        """Create refined sidebar UI with better visual hierarchy"""
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: #101010; }")

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        content.setLayout(layout)
        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)
        
        # Header Section
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 15)
        header_layout.setSpacing(8)
        header_frame.setLayout(header_layout)
        
        # Title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        title = QLabel("⚙️ Subtitle Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_font.setFamily("Segoe UI, Arial, sans-serif")
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; background: transparent;")
        
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Legacy toggle button
        self.legacy_toggle_btn = QToolButton()
        self.legacy_toggle_btn.setText("⇄")
        self.legacy_toggle_btn.setToolTip("Switch to Legacy Dialog")
        self.legacy_toggle_btn.setObjectName("LegacyToggleButton")
        self.legacy_toggle_btn.clicked.connect(lambda: self.toggle_legacy.emit())
        title_layout.addWidget(self.legacy_toggle_btn)
        
        header_layout.addLayout(title_layout)
        
        # Subtitle description
        desc = QLabel("Customize subtitle appearance and timing in real-time")
        desc.setStyleSheet("color: #888888; font-size: 12px; background: transparent;")
        desc.setWordWrap(True)
        header_layout.addWidget(desc)
        
        layout.addWidget(header_frame)
        
        # Typography Section
        typo_group = self._create_section("📝 Typography")
        
        # Font Family
        self._add_labeled_widget(typo_group, "Font Family", None)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.style.font_family))
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        typo_group.layout().addWidget(self.font_combo)
        
        # Font Size
        font_size_layout = self._create_slider_row(
            "Font Size", 8, 72, self.style.font_size, "pt"
        )
        self.font_size_spinner = font_size_layout[0]
        self.font_size_spinner.valueChanged.connect(self.on_font_size_changed)
        typo_group.layout().addLayout(font_size_layout[1])
        
        # Style Checkboxes
        style_row = QHBoxLayout()
        style_row.setSpacing(10)
        
        self.bold_check = QCheckBox("Bold")
        self.bold_check.setChecked(self.style.font_bold)
        self.bold_check.stateChanged.connect(self.on_style_changed)
        style_row.addWidget(self.bold_check)
        
        self.italic_check = QCheckBox("Italic")
        self.italic_check.setChecked(self.style.font_italic)
        self.italic_check.stateChanged.connect(self.on_style_changed)
        style_row.addWidget(self.italic_check)
        style_row.addStretch()
        
        typo_group.layout().addLayout(style_row)
        layout.addWidget(typo_group)
        
        # Colors Section
        colors_group = self._create_section("🎨 Colors")
        
        # Text Color
        text_color_row = self._create_color_row("Text Color", self.style.text_color)
        self.text_color_btn = text_color_row[0]
        self.text_color_btn.clicked.connect(lambda: self.pick_color("text"))
        colors_group.layout().addLayout(text_color_row[1])
        
        # Stroke Color
        stroke_color_row = self._create_color_row("Stroke Color", self.style.stroke_color)
        self.stroke_color_btn = stroke_color_row[0]
        self.stroke_color_btn.clicked.connect(lambda: self.pick_color("stroke"))
        colors_group.layout().addLayout(stroke_color_row[1])
        
        # Stroke Width
        stroke_width_layout = self._create_slider_row(
            "Stroke Width", 0, 10, self.style.stroke_width, "px"
        )
        self.stroke_width_slider = stroke_width_layout[2]
        self.stroke_value_label = stroke_width_layout[3]
        self.stroke_width_slider.valueChanged.connect(self.on_style_changed)
        colors_group.layout().addLayout(stroke_width_layout[1])
        
        # Background
        bg_row = QHBoxLayout()
        bg_row.setSpacing(10)
        
        self.bg_enable_check = QCheckBox("Background")
        self.bg_enable_check.setChecked(bool(self.style.background_color))
        self.bg_enable_check.stateChanged.connect(self.on_background_toggled)
        bg_row.addWidget(self.bg_enable_check)
        
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(60, 30)
        self.bg_color_btn.setObjectName("ColorButton")
        initial_bg_color = QColor(self.style.background_color or "#B4000000")
        self.update_color_button(
            self.bg_color_btn,
            initial_bg_color.name(QColor.NameFormat.HexArgb)
        )
        self.bg_color_btn.clicked.connect(lambda: self.pick_color("background"))
        self.bg_color_btn.setEnabled(self.bg_enable_check.isChecked())
        bg_row.addWidget(self.bg_color_btn)
        bg_row.addStretch()
        
        colors_group.layout().addLayout(bg_row)
        layout.addWidget(colors_group)
        
        # Position Section
        position_group = self._create_section("📍 Position")
        
        # Vertical Position
        v_pos_row = QHBoxLayout()
        v_pos_row.addWidget(QLabel("Vertical:"))
        self.pos_v_combo = QComboBox()
        self.pos_v_combo.addItems(["Top", "Center", "Bottom"])
        pos_map = {"top": 0, "center": 1, "bottom": 2}
        self.pos_v_combo.setCurrentIndex(pos_map.get(self.style.position_vertical, 2))
        self.pos_v_combo.currentTextChanged.connect(self.on_position_changed)
        v_pos_row.addWidget(self.pos_v_combo, 1)
        position_group.layout().addLayout(v_pos_row)
        
        # Horizontal Position
        h_pos_row = QHBoxLayout()
        h_pos_row.addWidget(QLabel("Horizontal:"))
        self.pos_h_combo = QComboBox()
        self.pos_h_combo.addItems(["Left", "Center", "Right"])
        pos_map_h = {"left": 0, "center": 1, "right": 2}
        self.pos_h_combo.setCurrentIndex(pos_map_h.get(self.style.position_horizontal, 1))
        self.pos_h_combo.currentTextChanged.connect(self.on_position_changed)
        h_pos_row.addWidget(self.pos_h_combo, 1)
        position_group.layout().addLayout(h_pos_row)
        
        # Vertical Margin
        margin_v_layout = self._create_slider_row(
            "Vertical Margin", 0, 300, self.style.margin_vertical, "px"
        )
        self.margin_v_spinner = margin_v_layout[0]
        self.margin_v_spinner.valueChanged.connect(self.on_margin_changed)
        position_group.layout().addLayout(margin_v_layout[1])
        
        # Horizontal Margin
        margin_h_layout = self._create_slider_row(
            "Horizontal Margin", 0, 300, self.style.margin_horizontal, "px"
        )
        self.margin_h_spinner = margin_h_layout[0]
        self.margin_h_spinner.valueChanged.connect(self.on_margin_changed)
        position_group.layout().addLayout(margin_h_layout[1])
        
        layout.addWidget(position_group)
        
        # Timing Section
        timing_group = self._create_section("⏱️ Timing")
        
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Timing Offset:"))
        self.timing_offset_spinner = QDoubleSpinBox()
        self.timing_offset_spinner.setRange(-3600.0, 3600.0)
        self.timing_offset_spinner.setDecimals(2)
        self.timing_offset_spinner.setSingleStep(0.1)
        self.timing_offset_spinner.setValue(float(self.style.timing_offset))
        self.timing_offset_spinner.setSuffix(" s")
        self.timing_offset_spinner.valueChanged.connect(self.on_timing_changed)
        timing_layout.addWidget(self.timing_offset_spinner, 1)
        timing_group.layout().addLayout(timing_layout)
        
        timing_hint = QLabel("Shift subtitles forward (+) or backward (−)")
        timing_hint.setStyleSheet("color: #666666; font-size: 11px; font-style: italic; background: transparent;")
        timing_hint.setWordWrap(True)
        timing_group.layout().addWidget(timing_hint)
        
        layout.addWidget(timing_group)
        
        # Add stretch at end
        layout.addStretch()
        
        # Apply refined styling
        self.setStyleSheet("""
            QWidget {
                background-color: #101010;
                color: #e0e0e0;
                font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
            }
            
            QFrame#HeaderFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #101010);
                border-radius: 8px;
                padding: 10px;
            }
            
            QGroupBox {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: bold;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background: #101010;
                border-radius: 4px;
                left: 10px;
                color: #4a9eff;
            }
            
            QLabel {
                color: #d0d0d0;
                background: transparent;
            }
            
            QComboBox, QFontComboBox {
                background: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 6px 10px;
                min-height: 25px;
            }
            
            QComboBox:hover, QFontComboBox:hover {
                border: 1px solid #4a9eff;
                background: #323232;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #888888;
                width: 0;
                height: 0;
                margin-right: 8px;
            }
            
            QSpinBox, QDoubleSpinBox {
                background: #2a2a2a;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 5px 8px;
                min-height: 25px;
            }
            
            QSpinBox:hover, QDoubleSpinBox:hover {
                border: 1px solid #4a9eff;
                background: #323232;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background: #3a3a3a;
                border: none;
                width: 18px;
                border-radius: 3px;
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background: #4a9eff;
            }
            
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #2a2a2a;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5aa0ff, stop:1 #3a80ff);
                border: 2px solid #2a5a9f;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6ab0ff, stop:1 #4a90ff);
                border: 2px solid #3a6aaf;
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a9eff, stop:1 #2a7edf);
                border-radius: 3px;
            }
            
            QCheckBox {
                color: #d0d0d0;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3a3a3a;
                border-radius: 4px;
                background: #2a2a2a;
            }
            
            QCheckBox::indicator:hover {
                border: 2px solid #4a9eff;
                background: #323232;
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a9eff, stop:1 #2a7edf);
                border: 2px solid #2a6acf;
            }
            
            QCheckBox::indicator:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5aa0ff, stop:1 #3a80ff);
            }
            
            QPushButton#ColorButton {
                border: 2px solid #3a3a3a;
                border-radius: 5px;
                min-width: 50px;
                min-height: 28px;
            }
            
            QPushButton#ColorButton:hover {
                border: 2px solid #4a9eff;
            }
            
            QToolButton#LegacyToggleButton {
                background: rgba(74, 158, 255, 0.15);
                color: #9ec0ff;
                border: 1px solid #3a6aaf;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 16px;
                font-weight: normal;
            }
            
            QToolButton#LegacyToggleButton:hover {
                background: rgba(74, 158, 255, 0.25);
                border: 1px solid #4a9eff;
            }
            
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 6px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
    
    def _create_section(self, title):
        """Create a styled section group"""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()
        group_layout.setSpacing(12)
        group_layout.setContentsMargins(15, 20, 15, 15)
        group.setLayout(group_layout)
        return group
    
    def _add_labeled_widget(self, parent, label_text, widget):
        """Add a label above a widget"""
        if label_text:
            label = QLabel(label_text)
            label.setStyleSheet("color: #b0b0b0; font-size: 12px; font-weight: 500; background: transparent;")
            parent.layout().addWidget(label)
        if widget:
            parent.layout().addWidget(widget)
    
    def _create_slider_row(self, label_text, min_val, max_val, current_val, suffix=""):
        """Create a row with label, slider, and spinbox"""
        row = QHBoxLayout()
        row.setSpacing(12)
        
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        row.addWidget(label)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(current_val)
        row.addWidget(slider, 1)
        
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(current_val)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setMinimumWidth(80)
        row.addWidget(spinbox)
        
        # Sync slider and spinbox
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        
        value_label = QLabel(str(current_val))
        value_label.setMinimumWidth(35)
        value_label.setStyleSheet("color: #888888; font-weight: bold; background: transparent;")
        
        return (spinbox, row, slider, value_label)
    
    def _create_color_row(self, label_text, color_hex):
        """Create a row for color selection"""
        row = QHBoxLayout()
        row.setSpacing(12)
        
        label = QLabel(label_text)
        label.setMinimumWidth(120)
        row.addWidget(label)
        
        color_btn = QPushButton()
        color_btn.setFixedSize(80, 30)
        color_btn.setObjectName("ColorButton")
        color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_color_button(color_btn, color_hex)
        row.addWidget(color_btn)
        
        color_value = QLabel(color_hex)
        color_value.setStyleSheet("color: #888888; font-size: 11px; font-family: monospace; background: transparent;")
        row.addWidget(color_value)
        row.addStretch()
        
        return (color_btn, row, color_value)
    
    def update_color_button(self, button, color_hex):
        """Update button appearance with color"""
        # Ensure color is valid
        color = QColor(color_hex)
        if not color.isValid():
            color = QColor("#ffffff")
        
        # Calculate if we need dark or light text
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        text_color = "#000000" if luminance > 0.5 else "#ffffff"
        
        button.setStyleSheet(f"""
            QPushButton#ColorButton {{
                background-color: {color.name()};
                color: {text_color};
                border: 2px solid #3a3a3a;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton#ColorButton:hover {{
                border: 2px solid #4a9eff;
            }}
        """)
    
    def pick_color(self, color_type):
        """Open color picker"""
        if color_type == "text":
            current_color = self.style.text_color
        elif color_type == "stroke":
            current_color = self.style.stroke_color
        else:
            current_color = self.style.background_color or "#000000B4"

        color = QColorDialog.getColor(QColor(current_color), self, f"Choose {color_type} color")
        if color.isValid():
            if color_type == "text":
                self.style.text_color = color.name()
                self.update_color_button(self.text_color_btn, self.style.text_color)
            elif color_type == "stroke":
                self.style.stroke_color = color.name()
                self.update_color_button(self.stroke_color_btn, self.style.stroke_color)
            else:
                hex_argb = color.name(QColor.NameFormat.HexArgb)
                self.style.background_color = hex_argb
                self.update_color_button(self.bg_color_btn, hex_argb)
            self.settings_changed.emit(self.style)
    
    def on_font_size_changed(self, value):
        """Handle font size change"""
        self.style.font_size = value
        self.settings_changed.emit(self.style)
    
    def on_font_changed(self, font):
        """Handle font family change"""
        if isinstance(font, QFont):
            self.style.font_family = font.family()
        else:
            self.style.font_family = str(font)
        self.settings_changed.emit(self.style)
    
    def on_style_changed(self):
        """Handle style changes (bold, italic, stroke width)"""
        self.style.font_bold = self.bold_check.isChecked()
        self.style.font_italic = self.italic_check.isChecked()
        self.style.stroke_width = self.stroke_width_slider.value()
        self.stroke_value_label.setText(str(self.style.stroke_width))
        self.settings_changed.emit(self.style)
    
    def on_position_changed(self):
        """Handle position changes"""
        pos_map_v = {0: "top", 1: "center", 2: "bottom"}
        pos_map_h = {0: "left", 1: "center", 2: "right"}
        self.style.position_vertical = pos_map_v[self.pos_v_combo.currentIndex()]
        self.style.position_horizontal = pos_map_h[self.pos_h_combo.currentIndex()]
        self.settings_changed.emit(self.style)
    
    def on_timing_changed(self):
        """Handle timing offset change"""
        self.style.timing_offset = float(self.timing_offset_spinner.value())
        self.settings_changed.emit(self.style)

    def on_background_toggled(self):
        """Enable/disable background color"""
        enabled = self.bg_enable_check.isChecked()
        self.bg_color_btn.setEnabled(enabled)
        if enabled and not self.style.background_color:
            self.style.background_color = "#B4000000"  # default semi-transparent black
            self.update_color_button(self.bg_color_btn, self.style.background_color)
        elif not enabled:
            self.style.background_color = ""
        self.settings_changed.emit(self.style)

    def on_margin_changed(self):
        """Handle margin updates"""
        self.style.margin_vertical = self.margin_v_spinner.value()
        self.style.margin_horizontal = self.margin_h_spinner.value()
        self.settings_changed.emit(self.style)
