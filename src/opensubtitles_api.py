"""
OpenSubtitles API Client
Handles authentication, subtitle search, and download from OpenSubtitles.com API
"""

import requests
import hashlib
import os
import struct
import gzip
import json
from typing import List, Dict, Optional
from pathlib import Path


class OpenSubtitlesAPI:
    """Client for OpenSubtitles.com API v1"""
    
    BASE_URL = "https://api.opensubtitles.com/api/v1"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the API client
        
        Args:
            api_key: Your OpenSubtitles API key (get one from https://www.opensubtitles.com/api)
        """
        self.api_key = api_key or os.environ.get('OPENSUBTITLES_API_KEY', '')
        self.session = requests.Session()
        self.session.headers.update({
            'Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'SubtitlePlayer v1.0'
        })
        self.token = None
        
    def login(self, username: str, password: str) -> bool:
        """
        Login to OpenSubtitles (optional, but increases rate limits)
        
        Args:
            username: OpenSubtitles username
            password: OpenSubtitles password
            
        Returns:
            bool: True if login successful
        """
        try:
            response = self.session.post(
                f"{self.BASE_URL}/login",
                json={'username': username, 'password': password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get('token')
            if self.token:
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False
    
    def calculate_video_hash(self, filepath: str) -> Optional[str]:
        """
        Calculate OpenSubtitles hash for a video file
        
        Args:
            filepath: Path to video file
            
        Returns:
            str: 16-character hexadecimal hash or None if failed
        """
        try:
            longlongformat = 'q'  # long long
            bytesize = struct.calcsize(longlongformat)
            
            with open(filepath, "rb") as f:
                filesize = os.path.getsize(filepath)
                hash_value = filesize
                
                if filesize < 65536 * 2:
                    return None
                
                # Read first 64KB
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF  # Remain as 64bit number
                
                # Read last 64KB
                f.seek(max(0, filesize - 65536), 0)
                for _ in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value &= 0xFFFFFFFFFFFFFFFF
                
                return "%016x" % hash_value
        except Exception as e:
            print(f"Error calculating hash: {e}")
            return None
    
    def search_subtitles(
        self, 
        video_path: str = None,
        query: str = None,
        languages: List[str] = None,
        video_hash: str = None,
        imdb_id: str = None
    ) -> List[Dict]:
        """
        Search for subtitles
        
        Args:
            video_path: Path to video file (for hash calculation)
            query: Movie/series name to search
            languages: List of language codes (e.g., ['en', 'es', 'pt-BR'])
            video_hash: Pre-calculated video hash
            imdb_id: IMDB ID of the movie/series
            
        Returns:
            List of subtitle dictionaries with metadata
        """
        params = {}
        
        # Calculate hash if video path provided
        if video_path and not video_hash:
            video_hash = self.calculate_video_hash(video_path)
        
        if video_hash:
            params['moviehash'] = video_hash
            
        if query:
            params['query'] = query
            
        if languages:
            params['languages'] = ','.join(languages)
        else:
            params['languages'] = 'en'
            
        if imdb_id:
            params['imdb_id'] = imdb_id
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/subtitles",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"Error searching subtitles: {e}")
            return []
    
    def download_subtitle(self, file_id: int, output_path: str) -> bool:
        """
        Download a subtitle file
        
        Args:
            file_id: The file_id from search results
            output_path: Where to save the subtitle file
            
        Returns:
            bool: True if download successful
        """
        try:
            # Get download link
            response = self.session.post(
                f"{self.BASE_URL}/download",
                json={'file_id': file_id}
            )
            response.raise_for_status()
            data = response.json()
            
            download_link = data.get('link')
            if not download_link:
                print("No download link received")
                return False
            
            # Download the file
            sub_response = self.session.get(download_link)
            sub_response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(sub_response.content)
            
            print(f"Subtitle downloaded successfully to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading subtitle: {e}")
            return False
    
    def get_subtitle_formats(self, subtitles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group subtitles by format
        
        Args:
            subtitles: List of subtitle dictionaries from search
            
        Returns:
            Dictionary grouped by format (srt, ass, vtt, etc.)
        """
        formats = {}
        for sub in subtitles:
            fmt = sub.get('attributes', {}).get('format', 'unknown')
            if fmt not in formats:
                formats[fmt] = []
            formats[fmt].append(sub)
        return formats
    
    def get_user_info(self) -> Optional[Dict]:
        """Get information about the logged-in user"""
        try:
            response = self.session.get(f"{self.BASE_URL}/infos/user")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
