"""
AI Subtitle Generation Dialog
User interface for generating subtitles using AI
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QProgressBar, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ai_subtitle_generator import AISubtitleGenerator, SubtitleSegment
from typing import List


class AIGenerationThread(QThread):
    """Background thread for AI subtitle generation"""
    
    progress_update = pyqtSignal(str, int)  # message, progress
    generation_complete = pyqtSignal(list)  # List[SubtitleSegment]
    generation_failed = pyqtSignal(str)  # error message
    
    def __init__(self, video_path, language, model_size):
        super().__init__()
        self.video_path = video_path
        self.language = language
        self.model_size = model_size
    
    def run(self):
        """Run AI generation"""
        try:
            generator = AISubtitleGenerator(self.model_size)
            
            # Progress callback
            def progress_cb(message, percent):
                self.progress_update.emit(message, percent)
            
            # Generate subtitles
            segments = generator.generate_subtitles(
                self.video_path,
                self.language if self.language != "auto" else None,
                progress_cb
            )
            
            if segments:
                self.generation_complete.emit(segments)
            else:
                self.generation_failed.emit("Failed to generate subtitles")
                
        except Exception as e:
            self.generation_failed.emit(str(e))


class AISubtitleDialog(QDialog):
    """Dialog for AI-powered subtitle generation"""
    
    LANGUAGES = {
        "Auto-detect": "auto",
        "English": "en",
        "Spanish": "es",
        "Portuguese": "pt",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "Chinese": "zh",
        "Arabic": "ar",
        "Hindi": "hi",
        "Dutch": "nl",
        "Polish": "pl",
        "Turkish": "tr"
    }
    
    MODEL_SIZES = {
        "Tiny (Fastest, 1GB RAM)": "tiny",
        "Base (Recommended, 1GB RAM)": "base",
        "Small (Better, 2GB RAM)": "small",
        "Medium (High Quality, 5GB RAM)": "medium",
        "Large (Best Quality, 10GB RAM)": "large"
    }
    
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.generated_segments = None
        self.generator = AISubtitleGenerator()
        
        self.init_ui()
        self.check_dependencies()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("AI Subtitle Generator - Powered by Whisper")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Info section
        info_group = QGroupBox("About AI Subtitle Generation")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "This feature uses OpenAI's Whisper model to automatically generate subtitles "
            "from the video's audio. Whisper provides state-of-the-art accuracy and supports "
            "99+ languages with proper punctuation and capitalization.\n\n"
            "⚡ First-time use will download the selected model (50MB-3GB).\n"
            "🎯 Processing time: ~30 seconds per minute of video.\n"
            "💻 Works completely offline after model download."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Audio Language:")
        self.language_combo = QComboBox()
        for lang_name, lang_code in self.LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.language_combo)
        config_layout.addLayout(lang_layout)
        
        # Model size selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model Size:")
        self.model_combo = QComboBox()
        for model_name, model_size in self.MODEL_SIZES.items():
            self.model_combo.addItem(model_name, model_size)
        self.model_combo.setCurrentIndex(1)  # Default to "base"
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        config_layout.addLayout(model_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Dependency status
        self.dependency_group = QGroupBox("Dependencies")
        self.dependency_layout = QVBoxLayout()
        self.dependency_group.setLayout(self.dependency_layout)
        layout.addWidget(self.dependency_group)
        
        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to generate subtitles")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log section (added for debugging)
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Preview section
        preview_group = QGroupBox("Preview (first 10 lines)")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Dependencies")
        self.install_btn.clicked.connect(self.show_install_instructions)
        button_layout.addWidget(self.install_btn)
        
        button_layout.addStretch()
        
        self.generate_btn = QPushButton("Generate Subtitles")
        self.generate_btn.clicked.connect(self.start_generation)
        button_layout.addWidget(self.generate_btn)
        
        self.save_btn = QPushButton("Save & Use")
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
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
            QComboBox, QTextEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 4px;
                border-radius: 4px;
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
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #7d7d7d;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
            }
        """)
    
    def check_dependencies(self):
        """Check and display dependency status"""
        # Clear existing widgets
        for i in reversed(range(self.dependency_layout.count())): 
            self.dependency_layout.itemAt(i).widget().deleteLater()
        
        status = self.generator.check_dependencies()
        
        all_installed = all(status.values())
        
        # Create status labels
        for dep, installed in status.items():
            label = QLabel(f"{'✓' if installed else '✗'} {dep.upper()}")
            label.setStyleSheet(f"color: {'#4CAF50' if installed else '#F44336'};")
            self.dependency_layout.addWidget(label)
        
        if all_installed:
            self.generate_btn.setEnabled(True)
            self.install_btn.setVisible(False)
        else:
            self.generate_btn.setEnabled(False)
            self.install_btn.setVisible(True)
    
    def show_install_instructions(self):
        """Show installation instructions"""
        instructions = self.generator.install_dependencies_command()
        
        QMessageBox.information(
            self,
            "Install Dependencies",
            "To use AI subtitle generation, install these dependencies:\n\n"
            f"{instructions}\n\n"
            "After installation, restart SubtitlePlayer."
        )
    
    def start_generation(self):
        """Start AI subtitle generation"""
        language = self.language_combo.currentData()
        model_size = self.model_combo.currentData()
        
        # Disable UI during generation
        self.generate_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        
        # Start generation thread
        self.gen_thread = AIGenerationThread(
            self.video_path,
            language,
            model_size
        )
        self.gen_thread.progress_update.connect(self.on_progress)
        self.gen_thread.generation_complete.connect(self.on_complete)
        self.gen_thread.generation_failed.connect(self.on_error)
        self.gen_thread.start()
    
    def on_progress(self, message, percent):
        """Handle progress update"""
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)
        
        # Add to log with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def on_complete(self, segments):
        """Handle generation completion"""
        self.generated_segments = segments
        
        # Log completion
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] ✓ Generation complete! {len(segments)} segments created")
        
        # Show preview
        preview_text = ""
        for i, segment in enumerate(segments[:10], 1):
            start = self._format_time(segment.start_time)
            end = self._format_time(segment.end_time)
            preview_text += f"{i}. [{start} → {end}]\n{segment.text}\n\n"
        
        if len(segments) > 10:
            preview_text += f"... and {len(segments) - 10} more segments"
        
        self.preview_text.setText(preview_text)
        
        # Enable save button
        self.save_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        
        self.status_label.setText(f"✓ Generated {len(segments)} subtitle segments!")
    
    def on_error(self, error):
        """Handle generation error"""
        # Log error
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] ❌ ERROR: {error}")
        
        self.status_label.setText(f"Error: {error}")
        self.generate_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Failed to generate subtitles:\n{error}"
        )
    
    def _format_time(self, seconds):
        """Format seconds to readable time"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def get_generated_segments(self):
        """Get the generated subtitle segments"""
        return self.generated_segments
    
    def get_subtitle_path(self):
        """Get path where subtitle should be saved"""
        from pathlib import Path
        video_path = Path(self.video_path)
        return str(video_path.with_suffix('.srt'))
