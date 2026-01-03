"""
Subtitle Search and Download Dialog
Search OpenSubtitles.com and download subtitles
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from .opensubtitles_api import OpenSubtitlesAPI


class SubtitleSearchThread(QThread):
    """Background thread for searching subtitles"""
    
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client, video_path, query, language):
        super().__init__()
        self.api_client = api_client
        self.video_path = video_path
        self.query = query
        self.language = language
    
    def run(self):
        """Run subtitle search"""
        try:
            results = self.api_client.search_subtitles(
                video_path=self.video_path,
                query=self.query,
                languages=[self.language] if self.language else None
            )
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class SubtitleDownloadThread(QThread):
    """Background thread for downloading subtitles"""
    
    download_complete = pyqtSignal(bool, str)
    
    def __init__(self, api_client, file_id, output_path):
        super().__init__()
        self.api_client = api_client
        self.file_id = file_id
        self.output_path = output_path
    
    def run(self):
        """Download subtitle"""
        try:
            success = self.api_client.download_subtitle(self.file_id, self.output_path)
            self.download_complete.emit(success, self.output_path)
        except Exception as e:
            self.download_complete.emit(False, str(e))


class SubtitleSearchDialog(QDialog):
    """Dialog for searching and downloading subtitles"""
    
    LANGUAGES = {
        "English": "en",
        "Spanish": "es",
        "Portuguese (Brazil)": "pt-BR",
        "Portuguese": "pt",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "Chinese (Simplified)": "zh-CN",
        "Arabic": "ar",
        "Dutch": "nl",
        "Polish": "pl",
        "Turkish": "tr"
    }
    
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.api_client = None
        self.search_results = []
        self.selected_subtitle_path = None
        
        self.init_ui()
        self.load_api_key()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Download Subtitles - OpenSubtitles.com")
        self.setModal(True)
        self.resize(900, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # API Key section
        api_group = QGroupBox("OpenSubtitles API Configuration")
        api_layout = QVBoxLayout()
        
        help_label = QLabel(
            "Get your free API key at: "
            '<a href="https://www.opensubtitles.com/api">https://www.opensubtitles.com/api</a>'
        )
        help_label.setOpenExternalLinks(True)
        api_layout.addWidget(help_label)
        
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your OpenSubtitles API key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        api_layout.addLayout(api_key_layout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Search section
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout()
        
        # Video file info
        video_name = os.path.basename(self.video_path)
        video_label = QLabel(f"Video: {video_name}")
        search_layout.addWidget(video_label)
        
        # Search query
        query_layout = QHBoxLayout()
        query_label = QLabel("Search:")
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Movie/Series name (optional, uses file hash by default)")
        query_layout.addWidget(query_label)
        query_layout.addWidget(self.query_input)
        search_layout.addLayout(query_layout)
        
        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItem("All Languages", "")
        for lang_name, lang_code in self.LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)
        self.language_combo.setCurrentText("English")
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_subtitles)
        lang_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(lang_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Results table
        results_label = QLabel("Search Results:")
        layout.addWidget(results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Language", "Release", "Downloads", "Rating", "Format", "Uploader"
        ])
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_btn = QPushButton("Download Selected")
        self.download_btn.clicked.connect(self.download_subtitle)
        self.download_btn.setEnabled(False)
        button_layout.addWidget(self.download_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Enable download button when row selected
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        
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
            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 6px;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                color: #cccccc;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #0e639c;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #cccccc;
                padding: 6px;
                border: none;
                font-weight: bold;
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
    
    def load_api_key(self):
        """Load saved API key"""
        from .config_manager import ConfigManager
        config_manager = ConfigManager()
        if config_manager.config.api_key:
            self.api_key_input.setText(config_manager.config.api_key)
    
    def save_api_key(self):
        """Save API key"""
        from .config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.config.api_key = self.api_key_input.text()
        config_manager.save_config()
    
    def search_subtitles(self):
        """Start subtitle search"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please enter your OpenSubtitles API key.\n\n"
                "Get one for free at: https://www.opensubtitles.com/api"
            )
            return
        
        # Save API key
        self.save_api_key()
        
        # Initialize API client
        self.api_client = OpenSubtitlesAPI(api_key)
        
        # Get search parameters
        query = self.query_input.text().strip()
        language = self.language_combo.currentData()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Searching...")
        self.search_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        
        # Start search thread
        self.search_thread = SubtitleSearchThread(
            self.api_client,
            self.video_path,
            query if query else None,
            language if language else None
        )
        self.search_thread.results_ready.connect(self.on_search_complete)
        self.search_thread.error_occurred.connect(self.on_search_error)
        self.search_thread.start()
    
    def on_search_complete(self, results):
        """Handle search completion"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        self.search_results = results
        
        if not results:
            self.status_label.setText("No subtitles found")
            return
        
        self.status_label.setText(f"Found {len(results)} subtitle(s)")
        
        # Populate table
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            attrs = result.get('attributes', {})
            
            # Language
            language = attrs.get('language', 'Unknown')
            self.results_table.setItem(i, 0, QTableWidgetItem(language))
            
            # Release
            release = attrs.get('release', 'N/A')
            self.results_table.setItem(i, 1, QTableWidgetItem(release))
            
            # Downloads
            downloads = str(attrs.get('download_count', 0))
            self.results_table.setItem(i, 2, QTableWidgetItem(downloads))
            
            # Rating
            rating = str(attrs.get('ratings', 0))
            self.results_table.setItem(i, 3, QTableWidgetItem(rating))
            
            # Format
            fmt = attrs.get('format', 'N/A')
            self.results_table.setItem(i, 4, QTableWidgetItem(fmt))
            
            # Uploader
            uploader = attrs.get('uploader', {}).get('name', 'Unknown')
            self.results_table.setItem(i, 5, QTableWidgetItem(uploader))
        
        self.results_table.resizeColumnsToContents()
    
    def on_search_error(self, error):
        """Handle search error"""
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Search Error", f"Failed to search subtitles:\n{error}")
    
    def on_selection_changed(self):
        """Handle table selection change"""
        self.download_btn.setEnabled(len(self.results_table.selectedItems()) > 0)
    
    def download_subtitle(self):
        """Download selected subtitle"""
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            return
        
        # Get file_id from result
        result = self.search_results[selected_row]
        file_id = result.get('attributes', {}).get('files', [{}])[0].get('file_id')
        
        if not file_id:
            QMessageBox.warning(self, "Error", "Could not get subtitle file ID")
            return
        
        # Determine output path
        video_path = Path(self.video_path)
        subtitle_format = result.get('attributes', {}).get('format', 'srt')
        output_path = video_path.with_suffix(f'.{subtitle_format}')
        
        # Check if file exists
        if output_path.exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"Subtitle file already exists:\n{output_path.name}\n\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Downloading...")
        self.download_btn.setEnabled(False)
        
        # Start download thread
        self.download_thread = SubtitleDownloadThread(
            self.api_client,
            file_id,
            str(output_path)
        )
        self.download_thread.download_complete.connect(self.on_download_complete)
        self.download_thread.start()
    
    def on_download_complete(self, success, path_or_error):
        """Handle download completion"""
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        
        if success:
            self.selected_subtitle_path = path_or_error
            self.status_label.setText(f"Downloaded successfully: {os.path.basename(path_or_error)}")
            QMessageBox.information(
                self,
                "Download Complete",
                f"Subtitle downloaded successfully:\n{os.path.basename(path_or_error)}"
            )
            self.accept()
        else:
            self.status_label.setText(f"Download failed: {path_or_error}")
            QMessageBox.critical(
                self,
                "Download Error",
                f"Failed to download subtitle:\n{path_or_error}"
            )
    
    def get_selected_subtitle_path(self):
        """Get path to downloaded subtitle"""
        return self.selected_subtitle_path
