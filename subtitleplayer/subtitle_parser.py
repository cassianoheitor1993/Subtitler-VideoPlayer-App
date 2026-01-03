"""
Subtitle Parser and Renderer
Supports SRT, VTT, and ASS/SSA subtitle formats
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from datetime import timedelta


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry"""
    index: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str
    style: Optional[dict] = None


class SubtitleParser:
    """Parse subtitle files in various formats"""
    
    @staticmethod
    def parse_srt_time(time_str: str) -> float:
        """Convert SRT timestamp to seconds"""
        # Format: HH:MM:SS,mmm
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    @staticmethod
    def parse_vtt_time(time_str: str) -> float:
        """Convert VTT timestamp to seconds"""
        # Format: HH:MM:SS.mmm or MM:SS.mmm
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
    
    @staticmethod
    def parse_ass_time(time_str: str) -> float:
        """Convert ASS/SSA timestamp to seconds"""
        # Format: H:MM:SS.CC (centiseconds)
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_parts = parts[2].split('.')
        seconds = int(sec_parts[0])
        centiseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        return hours * 3600 + minutes * 60 + seconds + centiseconds / 100
    
    def parse_srt(self, content: str) -> List[SubtitleEntry]:
        """Parse SRT format subtitles"""
        entries = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                index = int(lines[0])
                time_line = lines[1]
                text = '\n'.join(lines[2:])
                
                # Parse time line: HH:MM:SS,mmm --> HH:MM:SS,mmm
                time_match = re.match(r'(\S+)\s*-->\s*(\S+)', time_line)
                if time_match:
                    start_time = self.parse_srt_time(time_match.group(1))
                    end_time = self.parse_srt_time(time_match.group(2))
                    
                    # Remove HTML tags
                    text = re.sub(r'<[^>]+>', '', text)
                    
                    entries.append(SubtitleEntry(
                        index=index,
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
            except (ValueError, IndexError):
                continue
        
        return entries
    
    def parse_vtt(self, content: str) -> List[SubtitleEntry]:
        """Parse WebVTT format subtitles"""
        entries = []
        
        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
        
        blocks = re.split(r'\n\s*\n', content.strip())
        index = 1
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            # VTT can have optional cue identifier
            time_line_idx = 0
            if '-->' not in lines[0]:
                time_line_idx = 1
                if len(lines) < 3:
                    continue
            
            try:
                time_line = lines[time_line_idx]
                text = '\n'.join(lines[time_line_idx + 1:])
                
                # Parse time line
                time_match = re.match(r'(\S+)\s*-->\s*(\S+)', time_line)
                if time_match:
                    start_time = self.parse_vtt_time(time_match.group(1))
                    end_time = self.parse_vtt_time(time_match.group(2))
                    
                    # Remove VTT tags
                    text = re.sub(r'<[^>]+>', '', text)
                    
                    entries.append(SubtitleEntry(
                        index=index,
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    ))
                    index += 1
            except (ValueError, IndexError):
                continue
        
        return entries
    
    def parse_ass(self, content: str) -> List[SubtitleEntry]:
        """Parse ASS/SSA format subtitles"""
        entries = []
        index = 1
        
        # Find the Events section
        in_events = False
        format_line = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('[Events]'):
                in_events = True
                continue
            
            if in_events:
                if line.startswith('['):
                    break
                
                if line.startswith('Format:'):
                    format_line = line.replace('Format:', '').strip()
                    continue
                
                if line.startswith('Dialogue:') and format_line:
                    try:
                        # Parse the dialogue line
                        parts = line.replace('Dialogue:', '').strip().split(',')
                        
                        # Get format fields
                        fields = [f.strip() for f in format_line.split(',')]
                        
                        # Find indices
                        start_idx = fields.index('Start')
                        end_idx = fields.index('End')
                        text_idx = fields.index('Text')
                        
                        start_time = self.parse_ass_time(parts[start_idx])
                        end_time = self.parse_ass_time(parts[end_idx])
                        
                        # Text might contain commas, so join remaining parts
                        text = ','.join(parts[text_idx:])
                        
                        # Remove ASS formatting codes
                        text = re.sub(r'\{[^}]+\}', '', text)
                        text = text.replace('\\N', '\n')
                        
                        entries.append(SubtitleEntry(
                            index=index,
                            start_time=start_time,
                            end_time=end_time,
                            text=text
                        ))
                        index += 1
                    except (ValueError, IndexError):
                        continue
        
        return entries
    
    def parse_file(self, filepath: str) -> List[SubtitleEntry]:
        """
        Auto-detect format and parse subtitle file
        
        Args:
            filepath: Path to subtitle file
            
        Returns:
            List of SubtitleEntry objects
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                print(f"Could not decode file: {filepath}")
                return []
            
            # Detect format
            if content.startswith('WEBVTT'):
                return self.parse_vtt(content)
            elif '[Script Info]' in content or '[Events]' in content:
                return self.parse_ass(content)
            else:
                # Default to SRT
                return self.parse_srt(content)
                
        except Exception as e:
            print(f"Error parsing subtitle file: {e}")
            return []
    
    def get_subtitle_at_time(self, entries: List[SubtitleEntry], time_seconds: float) -> Optional[str]:
        """
        Get subtitle text for a specific time
        
        Args:
            entries: List of subtitle entries
            time_seconds: Current video time in seconds
            
        Returns:
            Subtitle text or None if no subtitle at this time
        """
        for entry in entries:
            if entry.start_time <= time_seconds <= entry.end_time:
                return entry.text
        return None
    
    def adjust_timing(self, entries: List[SubtitleEntry], offset_seconds: float) -> List[SubtitleEntry]:
        """
        Adjust subtitle timing by offset
        
        Args:
            entries: List of subtitle entries
            offset_seconds: Time offset in seconds (positive or negative)
            
        Returns:
            New list with adjusted times
        """
        adjusted = []
        for entry in entries:
            adjusted.append(SubtitleEntry(
                index=entry.index,
                start_time=max(0, entry.start_time + offset_seconds),
                end_time=max(0, entry.end_time + offset_seconds),
                text=entry.text,
                style=entry.style
            ))
        return adjusted
    
    @staticmethod
    def format_srt_time(seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    @staticmethod
    def format_vtt_time(seconds: float) -> str:
        """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def write_srt(self, entries: List[SubtitleEntry]) -> str:
        """
        Write subtitle entries to SRT format
        
        Args:
            entries: List of subtitle entries
            
        Returns:
            SRT formatted string
        """
        lines = []
        for entry in entries:
            lines.append(str(entry.index))
            start_time = self.format_srt_time(entry.start_time)
            end_time = self.format_srt_time(entry.end_time)
            lines.append(f"{start_time} --> {end_time}")
            lines.append(entry.text)
            lines.append("")  # Empty line between entries
        return "\n".join(lines)
    
    def write_vtt(self, entries: List[SubtitleEntry]) -> str:
        """
        Write subtitle entries to VTT format
        
        Args:
            entries: List of subtitle entries
            
        Returns:
            VTT formatted string
        """
        lines = ["WEBVTT", ""]
        for entry in entries:
            start_time = self.format_vtt_time(entry.start_time)
            end_time = self.format_vtt_time(entry.end_time)
            lines.append(f"{start_time} --> {end_time}")
            lines.append(entry.text)
            lines.append("")  # Empty line between entries
        return "\n".join(lines)
    
    def write_ass(self, entries: List[SubtitleEntry]) -> str:
        """
        Write subtitle entries to ASS format
        
        Args:
            entries: List of subtitle entries
            
        Returns:
            ASS formatted string
        """
        # Basic ASS header
        lines = [
            "[Script Info]",
            "Title: Translated Subtitles",
            "ScriptType: v4.00+",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        
        for entry in entries:
            start_time = self._format_ass_time(entry.start_time)
            end_time = self._format_ass_time(entry.end_time)
            # Replace newlines with \N for ASS format
            text = entry.text.replace('\n', '\\N')
            lines.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """Convert seconds to ASS timestamp format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
