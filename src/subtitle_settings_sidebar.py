"""
Professional Sidebar for Subtitle Settings
Allows real-time subtitle customization while watching video
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QColorDialog, QScrollArea,
    QFrame, QGroupBox, QSizePolicy, QDoubleSpinBox, QFontComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from config_manager import SubtitleStyle


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
        """Create sidebar UI"""
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        content.setLayout(layout)
        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)
        
        # Title
        title = QLabel("Subtitle Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.legacy_toggle_btn = QPushButton("Legacy View")
        self.legacy_toggle_btn.setObjectName("LegacyToggleButton")
        self.legacy_toggle_btn.clicked.connect(lambda: self.toggle_legacy.emit())
        header_layout.addWidget(self.legacy_toggle_btn)
        layout.addLayout(header_layout)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)
        
        # Font Size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spinner = QSpinBox()
        self.font_size_spinner.setRange(8, 72)
        self.font_size_spinner.setValue(self.style.font_size)
        self.font_size_spinner.valueChanged.connect(self.on_font_size_changed)
        font_layout.addWidget(self.font_size_spinner)
        layout.addLayout(font_layout)
        
        # Font Family
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.style.font_family))
        self.font_combo.currentFontChanged.connect(self.on_font_changed)
        font_family_layout.addWidget(self.font_combo)
        layout.addLayout(font_family_layout)
        
        # Bold
        self.bold_check = QCheckBox("Bold")
        self.bold_check.setChecked(self.style.font_bold)
        self.bold_check.stateChanged.connect(self.on_style_changed)
        layout.addWidget(self.bold_check)
        
        # Italic
        self.italic_check = QCheckBox("Italic")
        self.italic_check.setChecked(self.style.font_italic)
        self.italic_check.stateChanged.connect(self.on_style_changed)
        layout.addWidget(self.italic_check)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)
        
        # Text Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Text Color:"))
        self.text_color_btn = QPushButton()
        self.text_color_btn.setMaximumWidth(50)
        self.update_color_button(self.text_color_btn, self.style.text_color)
        self.text_color_btn.clicked.connect(lambda: self.pick_color("text"))
        color_layout.addWidget(self.text_color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Stroke Color
        stroke_color_layout = QHBoxLayout()
        stroke_color_layout.addWidget(QLabel("Stroke Color:"))
        self.stroke_color_btn = QPushButton()
        self.stroke_color_btn.setMaximumWidth(50)
        self.update_color_button(self.stroke_color_btn, self.style.stroke_color)
        self.stroke_color_btn.clicked.connect(lambda: self.pick_color("stroke"))
        stroke_color_layout.addWidget(self.stroke_color_btn)
        stroke_color_layout.addStretch()
        layout.addLayout(stroke_color_layout)
        
        # Stroke Width
        stroke_layout = QHBoxLayout()
        stroke_layout.addWidget(QLabel("Stroke Width:"))
        self.stroke_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.stroke_width_slider.setRange(0, 10)
        self.stroke_width_slider.setValue(self.style.stroke_width)
        self.stroke_width_slider.valueChanged.connect(self.on_style_changed)
        stroke_layout.addWidget(self.stroke_width_slider)
        self.stroke_value_label = QLabel(str(self.style.stroke_width))
        stroke_layout.addWidget(self.stroke_value_label)
        layout.addLayout(stroke_layout)
        
        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep3)
        
        # Background color and enable
        bg_layout = QHBoxLayout()
        self.bg_enable_check = QCheckBox("Background")
        self.bg_enable_check.setChecked(bool(self.style.background_color))
        self.bg_enable_check.stateChanged.connect(self.on_background_toggled)
        bg_layout.addWidget(self.bg_enable_check)
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setMaximumWidth(50)
        initial_bg_color = QColor(self.style.background_color or "#B4000000")
        self.update_color_button(
            self.bg_color_btn,
            initial_bg_color.name(QColor.NameFormat.HexArgb)
        )
        self.bg_color_btn.clicked.connect(lambda: self.pick_color("background"))
        self.bg_color_btn.setEnabled(self.bg_enable_check.isChecked())
        bg_layout.addWidget(self.bg_color_btn)
        bg_layout.addStretch()
        layout.addLayout(bg_layout)

        # Timing Offset
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("Timing Offset (s):"))
        self.timing_offset_spinner = QDoubleSpinBox()
        self.timing_offset_spinner.setRange(-3600.0, 3600.0)
        self.timing_offset_spinner.setDecimals(2)
        self.timing_offset_spinner.setSingleStep(0.1)
        self.timing_offset_spinner.setValue(float(self.style.timing_offset))
        self.timing_offset_spinner.setSuffix(" s")
        self.timing_offset_spinner.valueChanged.connect(self.on_timing_changed)
        timing_layout.addWidget(self.timing_offset_spinner)
        layout.addLayout(timing_layout)
        
        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep4)
        
        # Position Vertical
        pos_v_layout = QHBoxLayout()
        pos_v_layout.addWidget(QLabel("Vertical:"))
        self.pos_v_combo = QComboBox()
        self.pos_v_combo.addItems(["Top", "Center", "Bottom"])
        pos_map = {"top": 0, "center": 1, "bottom": 2}
        self.pos_v_combo.setCurrentIndex(pos_map.get(self.style.position_vertical, 2))
        self.pos_v_combo.currentTextChanged.connect(self.on_position_changed)
        pos_v_layout.addWidget(self.pos_v_combo)
        layout.addLayout(pos_v_layout)
        
        # Position Horizontal
        pos_h_layout = QHBoxLayout()
        pos_h_layout.addWidget(QLabel("Horizontal:"))
        self.pos_h_combo = QComboBox()
        self.pos_h_combo.addItems(["Left", "Center", "Right"])
        pos_map_h = {"left": 0, "center": 1, "right": 2}
        self.pos_h_combo.setCurrentIndex(pos_map_h.get(self.style.position_horizontal, 1))
        self.pos_h_combo.currentTextChanged.connect(self.on_position_changed)
        pos_h_layout.addWidget(self.pos_h_combo)
        layout.addLayout(pos_h_layout)

        # Margins
        margin_v_layout = QHBoxLayout()
        margin_v_layout.addWidget(QLabel("Vertical Margin:"))
        self.margin_v_spinner = QSpinBox()
        self.margin_v_spinner.setRange(0, 300)
        self.margin_v_spinner.setValue(self.style.margin_vertical)
        self.margin_v_spinner.setSuffix(" px")
        self.margin_v_spinner.valueChanged.connect(self.on_margin_changed)
        margin_v_layout.addWidget(self.margin_v_spinner)
        layout.addLayout(margin_v_layout)

        margin_h_layout = QHBoxLayout()
        margin_h_layout.addWidget(QLabel("Horizontal Margin:"))
        self.margin_h_spinner = QSpinBox()
        self.margin_h_spinner.setRange(0, 300)
        self.margin_h_spinner.setValue(self.style.margin_horizontal)
        self.margin_h_spinner.setSuffix(" px")
        self.margin_h_spinner.valueChanged.connect(self.on_margin_changed)
        margin_h_layout.addWidget(self.margin_h_spinner)
        layout.addLayout(margin_h_layout)
        
        # Add stretch at end
        layout.addStretch()
        
        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: #101010;
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
            }
            QComboBox, QFontComboBox, QSpinBox, QDoubleSpinBox, QSlider {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 3px;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #0d47a1;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QFrame {
                background-color: #555555;
            }
            QPushButton#LegacyToggleButton {
                background-color: transparent;
                color: #9ec0ff;
                border: 1px solid #1f4a8c;
                padding: 4px 10px;
            }
            QPushButton#LegacyToggleButton:hover {
                background-color: rgba(30, 90, 160, 0.3);
            }
        """)
    
    def update_color_button(self, button, color_hex):
        """Update button appearance with color"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 5px;
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
