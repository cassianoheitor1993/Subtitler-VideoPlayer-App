"""
Configuration and Metadata Manager
Handles user preferences, subtitle settings, and video metadata
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SubtitleStyle:
    """Subtitle styling preferences"""
    font_family: str = "Arial"
    font_size: int = 24
    font_bold: bool = False
    font_italic: bool = False
    text_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: int = 2
    background_color: str = "rgba(0, 0, 0, 180)"
    position_vertical: str = "bottom"  # top, center, bottom
    position_horizontal: str = "center"  # left, center, right
    margin_vertical: int = 50  # pixels from edge
    margin_horizontal: int = 20
    timing_offset: float = 0.0  # seconds


@dataclass
class AppConfig:
    """Application configuration"""
    api_key: str = ""
    username: str = ""
    remember_login: bool = False
    default_language: str = "en"
    auto_load_subtitles: bool = True
    recent_files_limit: int = 10
    subtitle_download_path: str = ""  # Empty means video directory
    volume: int = 100
    fullscreen: bool = False
    theme: str = "dark"


class ConfigManager:
    """Manage application configuration and metadata"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Directory to store config files (default: ~/.subtitleplayer)
        """
        if config_dir is None:
            home = Path.home()
            config_dir = home / ".subtitleplayer"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.recent_files_file = self.config_dir / "recent_files.json"
        self.metadata_dir = self.config_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        self.config = self.load_config()
        self.recent_files = self.load_recent_files()
    
    def load_config(self) -> AppConfig:
        """Load application configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                return AppConfig(**data)
            except Exception as e:
                print(f"Error loading config: {e}")
        return AppConfig()
    
    def save_config(self):
        """Save application configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def load_recent_files(self) -> list:
        """Load list of recent files"""
        if self.recent_files_file.exists():
            try:
                with open(self.recent_files_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading recent files: {e}")
        return []
    
    def save_recent_files(self):
        """Save list of recent files"""
        try:
            with open(self.recent_files_file, 'w') as f:
                json.dump(self.recent_files, f, indent=2)
        except Exception as e:
            print(f"Error saving recent files: {e}")
    
    def add_recent_file(self, filepath: str):
        """Add a file to recent files list"""
        # Remove if already exists
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        
        # Add to beginning
        self.recent_files.insert(0, filepath)
        
        # Limit size
        limit = self.config.recent_files_limit
        self.recent_files = self.recent_files[:limit]
        
        self.save_recent_files()
    
    def get_video_metadata_file(self, video_path: str) -> Path:
        """Get metadata file path for a video"""
        # Create unique filename from video path
        video_name = Path(video_path).stem
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in video_name)
        return self.metadata_dir / f"{safe_name}.json"
    
    def load_subtitle_style(self, video_path: str = None) -> SubtitleStyle:
        """
        Load subtitle style for a specific video or default
        
        Args:
            video_path: Path to video file (None for default)
            
        Returns:
            SubtitleStyle object
        """
        if video_path:
            metadata_file = self.get_video_metadata_file(video_path)
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                    if 'subtitle_style' in data:
                        return SubtitleStyle(**data['subtitle_style'])
                except Exception as e:
                    print(f"Error loading subtitle style: {e}")
        
        # Return default
        return SubtitleStyle()
    
    def save_subtitle_style(self, style: SubtitleStyle, video_path: str = None):
        """
        Save subtitle style for a specific video or as default
        
        Args:
            style: SubtitleStyle object
            video_path: Path to video file (None for default)
        """
        if video_path:
            metadata_file = self.get_video_metadata_file(video_path)
            
            # Load existing metadata
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except Exception:
                    pass
            
            # Update subtitle style
            metadata['subtitle_style'] = asdict(style)
            
            # Save
            try:
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                print(f"Error saving subtitle style: {e}")
    
    def load_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Load all metadata for a video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with metadata
        """
        metadata_file = self.get_video_metadata_file(video_path)
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading video metadata: {e}")
        return {}
    
    def save_video_metadata(self, video_path: str, metadata: Dict[str, Any]):
        """
        Save metadata for a video
        
        Args:
            video_path: Path to video file
            metadata: Dictionary with metadata
        """
        metadata_file = self.get_video_metadata_file(video_path)
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving video metadata: {e}")
    
    def get_subtitle_file_for_video(self, video_path: str) -> Optional[str]:
        """
        Get the last used subtitle file for a video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to subtitle file or None
        """
        metadata = self.load_video_metadata(video_path)
        return metadata.get('last_subtitle_file')
    
    def set_subtitle_file_for_video(self, video_path: str, subtitle_path: str):
        """
        Save the subtitle file used with a video
        
        Args:
            video_path: Path to video file
            subtitle_path: Path to subtitle file
        """
        metadata = self.load_video_metadata(video_path)
        metadata['last_subtitle_file'] = subtitle_path
        self.save_video_metadata(video_path, metadata)
