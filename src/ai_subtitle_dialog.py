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
from background_task_manager import BackgroundTaskManager, TaskType
from typing import List, Optional


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
    
    # Custom signal for when dialog is minimized to background
    minimized_to_background = pyqtSignal()
    
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
    
    def __init__(self, video_path, parent=None, task_manager: Optional[BackgroundTaskManager] = None):
        super().__init__(parent)
        self.video_path = video_path
        self.generated_segments = None
        self.generator = AISubtitleGenerator()
        self.task_manager = task_manager
        self.current_task_id = None
        self.minimized = False  # Track if dialog is running in background
        self.is_minimized = False  # Alias for video_player compatibility
        self._stored_geometry = None  # Saved geometry when minimized
        
        self.init_ui()
        self.check_dependencies()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("AI Subtitle Generator - Powered by Whisper")
        self.setModal(False)  # Non-modal to allow minimize
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowCloseButtonHint)
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
        
        # Minimize button (only if task_manager available)
        self.minimize_btn = QPushButton("⬇ Minimize")
        self.minimize_btn.clicked.connect(self.minimize_to_background)
        self.minimize_btn.setVisible(False)  # Hidden by default
        self.minimize_btn.setToolTip("Continue in background while you watch the video")
        button_layout.addWidget(self.minimize_btn)
        
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
        
        # Always show minimize button during generation
        self.minimize_btn.setVisible(True)
        
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
        
        # Update progress indicator if minimized
        if self.minimized and self.parent():
            try:
                if hasattr(self.parent(), 'ai_progress_indicator') and self.parent().ai_progress_indicator:
                    # Format: "Processing: 45% - Step 23/50"
                    self.parent().ai_progress_indicator.update_status(f"{percent}% - {message}")
            except Exception:
                pass
        
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
        
        # ALWAYS update preview - don't wait for restore
        # This ensures the data is ready when user restores
        preview_text = ""
        for i, segment in enumerate(segments[:10], 1):
            start = self._format_time(segment.start_time)
            end = self._format_time(segment.end_time)
            preview_text += f"{i}. [{start} → {end}]\n{segment.text}\n\n"
        
        if len(segments) > 10:
            preview_text += f"... and {len(segments) - 10} more segments"
        
        self.preview_text.setText(preview_text)
        
        # Enable save button and hide minimize button
        self.save_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        self.minimize_btn.setVisible(False)
        
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
        self.minimize_btn.setVisible(False)
        
        from PyQt6.QtWidgets import QMessageBox
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
    
    def minimize_to_background(self):
        """Minimize dialog and continue in background"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check if generation is running
        if not hasattr(self, 'gen_thread') or not self.gen_thread.isRunning():
            return
        
        self.minimized = True
        self.is_minimized = True  # Also set alias for video_player
        
        # Log the minimization
        self.log_text.append(f"[{timestamp}] ⬇ Minimized - continuing in background...")
        
        # Notify parent (video player) to show status
        if self.parent():
            try:
                from pathlib import Path
                video_name = Path(self.video_path).name
                self.parent().statusBar().showMessage(f"🤖 AI generation running in background: {video_name}", 5000)
            except Exception:
                pass
        
        # Save geometry and move off-screen instead of hiding (prevents repaint glitches)
        if self._stored_geometry is None:
            self._stored_geometry = self.geometry()

        # Hide the dialog instead of moving off-screen to keep UI responsive
        self.hide()
        self.setEnabled(True)
        self.setWindowOpacity(1.0)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Ensure parent regains activation so menus remain usable
        if self.parent():
            try:
                parent = self.parent()
                parent.setEnabled(True)
                if hasattr(parent, 'menuBar'):
                    parent.menuBar().setEnabled(True)
                parent.activateWindow()
                parent.raise_()
                parent.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            except Exception:
                pass
        
        # Emit signal for parent to show indicator
        self.minimized_to_background.emit()
    
    def restore_from_background(self):
        """Restore dialog from background"""
        self.minimized = False
        self.is_minimized = False  # Also reset alias
        
        # Restore geometry and visual state
        if self._stored_geometry is not None:
            self.setGeometry(self._stored_geometry)
        self.setWindowOpacity(1.0)
        self.setEnabled(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.update()
        self.repaint()
        if hasattr(self, 'preview_text') and self.preview_text:
            self.preview_text.viewport().update()
            self.preview_text.viewport().repaint()
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.viewport().update()
            self.log_text.viewport().repaint()
        self._stored_geometry = None
        
        # Clear status bar message
        if self.parent():
            try:
                self.parent().statusBar().showMessage("Ready")
            except:
                pass
    
    def _run_in_background(self, progress_callback, cancel_check):
        """Execute generation in background (for BackgroundTaskManager)"""
        try:
            language = self.language_combo.currentData()
            model_size = self.model_combo.currentData()
            
            generator = AISubtitleGenerator(model_size)
            
            # Adapt progress callback for BackgroundTaskManager
            def adapted_progress(message, percent):
                if cancel_check():
                    raise InterruptedError("Task cancelled by user")
                progress_callback(message, percent)
                # Also update UI if dialog is visible
                if not self.minimized:
                    self.on_progress(message, percent)
            
            # Generate subtitles
            segments = generator.generate_subtitles(
                self.video_path,
                language if language != "auto" else None,
                adapted_progress
            )
            
            return segments
            
        except InterruptedError:
            raise
        except Exception as e:
            raise RuntimeError(f"AI generation failed: {str(e)}")
    
    def _on_background_complete(self, result):
        """Handle background task completion"""
        self.generated_segments = result
        
        # Update UI
        if not self.minimized:
            self.on_complete(result)
        else:
            # If minimized, just enable the save button for when user returns
            self.save_btn.setEnabled(True)
        
        # Show notification
        if self.parent():
            # Parent will show notification via StatusIndicatorWidget
            pass
    
    def _on_background_error(self, error):
        """Handle background task error"""
        if not self.minimized:
            self.on_error(str(error))
        else:
            # Log error even if minimized
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] ❌ Background error: {error}")
    
    def changeEvent(self, event):
        """Handle window state changes - catch minimize from native button"""
        from PyQt6.QtCore import QEvent, Qt
        
        if event.type() == QEvent.Type.WindowStateChange:
            # Check if window was minimized using native button
            if self.windowState() & Qt.WindowState.WindowMinimized:
                # If generation is running, minimize to background instead
                if hasattr(self, 'gen_thread') and self.gen_thread.isRunning():
                    event.ignore()
                    # Restore window state to normal first
                    self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
                    # Then minimize to background
                    self.minimize_to_background()
                    return
        
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """Handle dialog close - ask to cancel if generation is running"""
        # Check if generation thread is actually running
        if hasattr(self, 'gen_thread') and self.gen_thread.isRunning():
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Cancel Generation?",
                "AI subtitle generation is still running. Cancel it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Stop the thread
                try:
                    self.gen_thread.terminate()
                    self.gen_thread.wait()
                except:
                    pass
                event.accept()
            else:
                # Don't close, just minimize to background
                event.ignore()
                self.minimize_to_background()
                return
        
        super().closeEvent(event)
