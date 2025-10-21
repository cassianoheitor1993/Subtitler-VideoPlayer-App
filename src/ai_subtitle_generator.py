"""
AI Subtitle Generator Module
Integrates open-source speech-to-text models for automatic subtitle generation
Optimized for low-memory systems and CPU fallback

Recommended Open Source Options:
1. Whisper by OpenAI - Best overall accuracy
2. Vosk - Fast, lightweight, offline
3. DeepSpeech (Mozilla) - Good for English
4. wav2vec 2.0 (Facebook) - State-of-the-art accuracy
"""

import os
import subprocess
import gc
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
import json

import logging
logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """Represents a subtitle segment with timing"""
    start_time: float
    end_time: float
    text: str
    confidence: float = 0.0


class AISubtitleGenerator:
    """
    AI-powered subtitle generator using Whisper
    Optimized for memory efficiency and CPU fallback
    
    Whisper is recommended because:
    - State-of-the-art accuracy
    - Supports 99+ languages
    - Built-in punctuation and capitalization
    - Automatic timestamp generation
    - Open source and free
    - Works offline after model download
    """
    
    def __init__(self, model_size: str = "base", resource_manager=None):
        """
        Initialize AI subtitle generator
        
        Args:
            model_size: Whisper model size
                - tiny: Fastest, least accurate (~1GB RAM, CPU-friendly)
                - base: Good balance (~1GB RAM) [RECOMMENDED for low-end hardware]
                - small: Better accuracy (~2GB RAM)
                - medium: High accuracy (~5GB RAM)
                - large: Best accuracy (~10GB RAM)
            resource_manager: Optional ResourceManager for hardware optimization
        """
        # Import here to avoid circular dependency
        if resource_manager is None:
            from resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
        
        self.resource_manager = resource_manager
        
        # Auto-select model size based on hardware if using default
        if model_size == "base":
            recommended = self.resource_manager.get_recommended_model_size()
            logger.info(f"Auto-selected model size '{recommended}' based on hardware")
            self.model_size = recommended
        else:
            self.model_size = model_size
        
        self.model = None
        self.model_loaded = False
        self._whisper_config = self.resource_manager.get_whisper_config()
        self._use_cpu = not self.resource_manager.resources.use_gpu
        
        logger.info(f"AI Generator initialized - Model: {self.model_size}, "
                   f"Device: {self._whisper_config['device']}, "
                   f"FP16: {self._whisper_config['fp16']}")
    
    def check_dependencies(self) -> dict:
        """
        Check if required dependencies are installed
        
        Returns:
            dict with status of each dependency
        """
        status = {
            'whisper': False,
            'ffmpeg': False,
            'torch': False
        }
        
        try:
            import whisper
            status['whisper'] = True
        except ImportError:
            pass
        
        try:
            import torch
            status['torch'] = True
        except ImportError:
            pass
        
        # Check ffmpeg
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            status['ffmpeg'] = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return status
    
    def install_dependencies_command(self) -> str:
        """
        Get command to install dependencies
        
        Returns:
            Shell command string
        """
        return """
# Install system dependencies
sudo apt install ffmpeg

# Install Python packages
pip install openai-whisper torch torchvision torchaudio

# OR for CPU-only (lighter):
pip install openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
"""
    
    def load_model(self, progress_callback: Optional[Callable] = None):
        """
        Load Whisper model with hardware-optimized settings
        
        Args:
            progress_callback: Optional callback for download progress
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import whisper
            import torch
            
            if progress_callback:
                progress_callback("Checking hardware capabilities...", 0)
            
            device = self._whisper_config['device']
            resources = self.resource_manager.resources
            
            # Inform user about hardware detection
            if resources.use_gpu:
                msg = f"🚀 GPU Acceleration: {resources.gpu.name} ({resources.gpu.memory_total}MB)"
                if resources.use_fp16:
                    msg += " + FP16 (2x faster!)"
                if progress_callback:
                    progress_callback(msg, 10)
                logger.info(msg)
            else:
                msg = f"CPU Mode: {resources.cpu_count_physical} cores @ {resources.cpu_freq_max:.0f}MHz"
                if progress_callback:
                    progress_callback(msg, 10)
                logger.info(msg)
            
            if progress_callback:
                progress_callback(f"Loading Whisper '{self.model_size}' model...", 20)
            
            # Load model with explicit device
            self.model = whisper.load_model(self.model_size, device=device)
            self.model_loaded = True
            
            # Optimize model for inference
            self.model.eval()  # Set to evaluation mode
            
            # Keep model in FP32 to avoid type conversion errors
            # FP16 can cause "expected Float but found Half" errors in some PyTorch versions
            self.model.float()
            logger.info("Model using FP32 (Full Precision) for stability")
            
            # Force garbage collection after loading model
            gc.collect()
            if device == "cuda":
                torch.cuda.empty_cache()
            
            if progress_callback:
                progress_callback(f"✓ Model loaded successfully on {device.upper()}", 100)
            
            logger.info(f"Model loaded: {self.model_size} on {device}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            if progress_callback:
                progress_callback(f"❌ Error loading model: {str(e)}", 0)
            return False
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model:
            del self.model
            self.model = None
            self.model_loaded = False
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
    
    def extract_audio(self, video_path: str, output_audio: str) -> bool:
        """
        Extract audio from video file using efficient settings
        
        Args:
            video_path: Path to video file
            output_audio: Path to save extracted audio
            
        Returns:
            True if successful
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM audio
                '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
                '-ac', '1',  # Mono (reduces memory usage)
                '-y',  # Overwrite
                output_audio
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5 minutes max
            )
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False
    
    def generate_subtitles(
        self,
        video_path: str,
        language: str = None,
        progress_callback: Optional[Callable] = None
    ) -> Optional[List[SubtitleSegment]]:
        """
        Generate subtitles from video
        
        Args:
            video_path: Path to video file
            language: Language code (e.g., 'en', 'es', 'pt') or None for auto-detect
            progress_callback: Optional callback(message, progress_percent)
            
        Returns:
            List of SubtitleSegment objects or None if failed
        """
        if not self.model_loaded:
            if progress_callback:
                progress_callback("Loading model...", 0)
            if not self.load_model(progress_callback):
                return None
        
        audio_path = None
        try:
            # Extract audio from video
            import time
            start_time = time.time()
            
            if progress_callback:
                progress_callback("📹 Extracting audio from video...", 10)
            
            audio_path = Path(video_path).with_suffix('.wav')
            if not self.extract_audio(video_path, str(audio_path)):
                if progress_callback:
                    progress_callback("❌ Failed to extract audio", 0)
                return None
            
            elapsed = int(time.time() - start_time)
            if progress_callback:
                progress_callback(f"✓ Audio extracted ({elapsed}s)", 20)
            
            # Transcribe with Whisper - with hardware-optimized options
            if progress_callback:
                import torch
                device_str = self._whisper_config['device'].upper()
                if self.resource_manager.resources.use_gpu:
                    gpu_name = self.resource_manager.resources.gpu.name
                    progress_callback(f"🚀 Transcribing with {gpu_name} acceleration...", 30)
                else:
                    progress_callback(f"🤖 Transcribing on CPU ({self.resource_manager.resources.cpu_count_physical} cores)...", 30)
            
            # Use optimized settings from ResourceManager
            # Disable FP16 to avoid "expected Float but found Half" errors
            # FP16 can cause compatibility issues with some PyTorch operations
            options = {
                'task': 'transcribe',
                'verbose': False,
                'fp16': False,  # Disabled to prevent type conversion errors
                'beam_size': self._whisper_config['beam_size'],
                'best_of': self._whisper_config['best_of'],
                'condition_on_previous_text': self._whisper_config['condition_on_previous_text'],
                'compression_ratio_threshold': self._whisper_config['compression_ratio_threshold'],
                'no_speech_threshold': self._whisper_config['no_speech_threshold'],
            }
            
            # Add threads for CPU mode
            if self._use_cpu and self._whisper_config['threads'] > 0:
                options['threads'] = self._whisper_config['threads']
                logger.info(f"Using {options['threads']} CPU threads for transcription")
            
            if language:
                options['language'] = language
            
            logger.info(f"Whisper options: {options}")
            
            transcribe_start = time.time()
            result = self.model.transcribe(str(audio_path), **options)
            transcribe_elapsed = int(time.time() - transcribe_start)
            
            # Calculate speed metrics
            video_duration = result.get('duration', 0) or (transcribe_elapsed * 2)  # Fallback estimate
            speed_factor = video_duration / transcribe_elapsed if transcribe_elapsed > 0 else 0
            
            if progress_callback:
                progress_callback(f"✓ Transcription complete ({transcribe_elapsed}s) - {speed_factor:.1f}x realtime", 70)
            
            logger.info(f"Transcription took {transcribe_elapsed}s for {video_duration:.1f}s video ({speed_factor:.1f}x realtime)")
            
            # Clean up audio file immediately to free disk space
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    audio_path = None
            except Exception as e:
                print(f"Warning: Could not remove temp audio file: {e}")
            
            # Convert to subtitle segments
            if progress_callback:
                progress_callback("📝 Processing subtitle segments...", 80)
            
            segments = []
            for segment in result['segments']:
                segments.append(SubtitleSegment(
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'].strip(),
                    confidence=segment.get('confidence', 0.0)
                ))
            
            # Clear result to free memory
            del result
            gc.collect()
            
            if progress_callback:
                progress_callback(f"✓ Generated {len(segments)} subtitle segments!", 100)
            
            return segments
            
        except Exception as e:
            print(f"Error generating subtitles: {e}")
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}", 0)
            return None
        finally:
            # Ensure cleanup even if there's an error
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            except:
                pass
            # Force garbage collection
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
    
    def save_to_srt(self, segments: List[SubtitleSegment], output_path: str) -> bool:
        """
        Save subtitle segments to SRT file
        
        Args:
            segments: List of SubtitleSegment objects
            output_path: Path to save SRT file
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    # Index
                    f.write(f"{i}\n")
                    
                    # Timestamp
                    start = self._format_timestamp(segment.start_time)
                    end = self._format_timestamp(segment.end_time)
                    f.write(f"{start} --> {end}\n")
                    
                    # Text
                    f.write(f"{segment.text}\n")
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error saving SRT: {e}")
            return False
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class VoskSubtitleGenerator:
    """
    Alternative: Vosk-based subtitle generator (lighter, faster)
    
    Vosk advantages:
    - Very fast (real-time capable)
    - Small models (50MB-1GB)
    - Works offline
    - Low resource usage
    - Good for real-time applications
    
    Vosk disadvantages:
    - Lower accuracy than Whisper
    - Less sophisticated punctuation
    - Fewer languages
    """
    
    def __init__(self, model_path: str):
        """
        Initialize Vosk generator
        
        Args:
            model_path: Path to Vosk model directory
                Download from: https://alphacephei.com/vosk/models
        """
        self.model_path = model_path
        self.model = None
    
    def check_dependencies(self) -> bool:
        """Check if Vosk is installed"""
        try:
            import vosk
            return True
        except ImportError:
            return False
    
    def install_command(self) -> str:
        """Get installation command"""
        return "pip install vosk"
    
    # Implementation similar to Whisper but with Vosk API
    # Left as exercise - Whisper is recommended for better quality


# Comparison of AI Models for Subtitle Generation

"""
RECOMMENDED: OpenAI Whisper
================================
✓ Best overall accuracy
✓ 99+ languages supported
✓ Excellent punctuation and capitalization
✓ Handles accents and dialects well
✓ MIT License (open source)
✓ Active development
✓ Word-level timestamps available

Models:
- tiny: ~39M params, ~32x faster than real-time
- base: ~74M params, ~16x faster (RECOMMENDED for balance)
- small: ~244M params, ~6x faster
- medium: ~769M params, ~2x faster
- large: ~1550M params, ~1x (best quality)

Installation:
    pip install openai-whisper torch


ALTERNATIVE 1: Vosk
===================
✓ Very fast and lightweight
✓ Works offline
✓ Real-time capable
✓ Small models (50MB-1GB)
✗ Lower accuracy
✗ Basic punctuation
✗ Limited languages

Best for: Resource-constrained systems, real-time needs

Installation:
    pip install vosk
    # Download model from https://alphacephei.com/vosk/models


ALTERNATIVE 2: wav2vec 2.0 (Facebook)
=====================================
✓ State-of-the-art accuracy
✓ Good for fine-tuning
✗ Requires more setup
✗ No built-in punctuation
✗ Need separate punctuation model

Best for: Research, custom training

Installation:
    pip install transformers soundfile


ALTERNATIVE 3: DeepSpeech (Mozilla)
===================================
✗ Project discontinued (2021)
✗ Not recommended for new projects


RECOMMENDATION FOR SUBTITLEPLAYER:
===================================
Use Whisper "base" model:
- Best balance of speed and accuracy
- One-line installation
- Works out of the box
- Handles multiple languages
- Professional quality results
- ~1GB RAM usage
- ~30 seconds processing per minute of audio

For real-time or very fast needs: Use Vosk
For best possible quality: Use Whisper "large"
"""
