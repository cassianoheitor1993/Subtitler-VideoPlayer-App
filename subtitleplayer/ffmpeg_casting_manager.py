"""FFmpeg-based HLS casting manager for reliable network streaming."""

from __future__ import annotations

import json
import os
import shutil
import signal
import socket
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Dict, Optional

import logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_ARCHIVE_DIR = PROJECT_ROOT / "logs" / "cast_failures"


@dataclass
class FFmpegCastingConfig:
    """Configuration for FFmpeg HLS casting."""
    
    host: str = "0.0.0.0"
    port: int = 8080
    hls_time: int = 2  # Segment duration in seconds
    hls_list_size: int = 5  # Number of segments to keep
    startup_timeout: int = 60  # Seconds to wait for initial manifest
    target_height: int = 1080  # Downscale video height (maintains aspect ratio)
    video_crf: int = 21  # Perceptual quality target for H.264
    video_preset: str = "veryfast"  # x264 preset balancing quality vs speed
    video_profile: str = "high"  # H.264 profile for broad device support
    video_level: str = "4.1"  # H.264 level compatible with 1080p playback
    video_maxrate: str = "6000k"  # Peak bitrate cap for HLS segments
    video_bufsize: str = "12000k"  # VBV buffer size to pair with maxrate
    audio_bitrate: str = "192k"  # Target AAC bitrate
    audio_channels: int = 2  # Downmix to stereo for device compatibility


class FFmpegCastingError(RuntimeError):
    """Raised when FFmpeg casting actions fail."""


class FFmpegCastingManager:
    """Manage FFmpeg HLS stream output sessions with hardware acceleration."""

    def __init__(self, resource_manager=None):
        """
        Initialize casting manager with hardware optimization
        
        Args:
            resource_manager: Optional ResourceManager for hardware optimization
        """
        # Import here to avoid circular dependency
        if resource_manager is None:
            from .resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
        
        self.resource_manager = resource_manager
        self._ffmpeg_config = self.resource_manager.get_ffmpeg_config()
        
        logger.info(f"FFmpeg optimizer: codec={self._ffmpeg_config.get('video_codec', 'libx264')}, "
                   f"threads={self._ffmpeg_config['threads']}, "
                   f"preset={self._ffmpeg_config['preset']}")
        
        self._ffmpeg_process: Optional[subprocess.Popen] = None
        self._http_server_process: Optional[subprocess.Popen] = None
        self._hls_dir: Optional[Path] = None
        self._active_config: Optional[FFmpegCastingConfig] = None
        self._active_video_path: Optional[str] = None
        self._active_subtitle_path: Optional[str] = None
        self._ffmpeg_log_handle: Optional[IO[str]] = None
        self._http_log_handle: Optional[IO[str]] = None
        self._ffmpeg_log_path: Optional[Path] = None
        self._http_log_path: Optional[Path] = None

    @property
    def is_casting(self) -> bool:
        """Check if casting is currently active."""
        return (
            self._ffmpeg_process is not None 
            and self._ffmpeg_process.poll() is None
            and self._http_server_process is not None
            and self._http_server_process.poll() is None
        )

    @property
    def url(self) -> Optional[str]:
        """Get the current streaming URL."""
        if not self.is_casting or not self._active_config:
            return None
        
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "localhost"
        
        return f"http://{local_ip}:{self._active_config.port}/stream.m3u8"

    def _terminate_previous_session(self, port: int) -> None:
        """Kill any lingering FFmpeg/HTTP processes from prior sessions."""
        self._stop_processes_from_pid_file()

        pkill_path = shutil.which("pkill")
        if not pkill_path:
            return

        patterns = [
            "ffmpeg.*stream.m3u8",
            f"http.server {port}",
            f"hls_http_server.py {port}",
        ]

        for pattern in patterns:
            try:
                subprocess.run(
                    [pkill_path, "-f", pattern],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                continue

    def _stop_processes_from_pid_file(self) -> None:
        """Terminate processes recorded in the PID file if they are still alive."""
        pid_file = Path("/tmp/subtitle_player_stream.pids")
        if not pid_file.exists():
            return

        try:
            tokens = pid_file.read_text().strip().split()
        except Exception:
            tokens = []

        for token in tokens:
            try:
                pid = int(token)
            except ValueError:
                continue
            self._terminate_pid(pid)

        try:
            pid_file.unlink()
        except Exception:
            pass

    @staticmethod
    def _terminate_pid(pid: int) -> None:
        """Attempt to terminate a process by PID."""
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                return
            except PermissionError:
                return

            time.sleep(0.1)
            if not FFmpegCastingManager._is_pid_running(pid):
                return

    @staticmethod
    def _is_pid_running(pid: int) -> bool:
        """Check if a PID is still running."""
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def start_hls_stream(
        self,
        video_path: str,
        config: Optional[FFmpegCastingConfig] = None,
        subtitle_path: Optional[str] = None,
    ) -> str:
        """
        Start FFmpeg HLS streaming.
        
        Args:
            video_path: Path to the video file to stream
            config: Optional casting configuration
            
        Returns:
            The streaming URL
            
        Raises:
            FFmpegCastingError: If streaming fails to start
        """
        if self.is_casting:
            raise FFmpegCastingError("Casting session already active")

        if not os.path.exists(video_path):
            raise FFmpegCastingError(f"Video file not found: {video_path}")

        cfg = config or FFmpegCastingConfig()

        self._terminate_previous_session(cfg.port)

        subtitle_filter_arg: Optional[str] = None
        if subtitle_path:
            normalized_subtitle = os.path.abspath(subtitle_path)
            if not os.path.exists(normalized_subtitle):
                raise FFmpegCastingError(f"Subtitle file not found: {normalized_subtitle}")
            subtitle_filter_arg = self._build_subtitle_filter(normalized_subtitle)
            self._active_subtitle_path = normalized_subtitle
        else:
            self._active_subtitle_path = None
        
        # Create HLS directory
        self._hls_dir = Path("/tmp/subtitle_player_hls")
        self._hls_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up old segments
        for old_file in self._hls_dir.glob("*"):
            try:
                old_file.unlink()
            except Exception:
                pass

        # Start FFmpeg HLS encoder with hardware optimization
        ffmpeg_cmd = [
            "ffmpeg",
            "-re",  # Read input at native framerate
            "-stream_loop", "-1",  # Loop indefinitely
        ]
        
        # Add hardware acceleration if available
        hwaccel = self._ffmpeg_config.get('hwaccel')
        if hwaccel:
            ffmpeg_cmd.extend(["-hwaccel", hwaccel])
            if hwaccel == "cuda":
                ffmpeg_cmd.extend(["-hwaccel_output_format", "cuda"])
                logger.info("Using NVIDIA CUDA hardware acceleration")
        
        ffmpeg_cmd.extend(["-i", video_path])

        video_filters: list[str] = []
        if subtitle_filter_arg:
            video_filters.append(subtitle_filter_arg)

        if cfg.target_height:
            video_filters.append(f"scale=-2:{cfg.target_height}")

        video_filters.append("format=yuv420p")

        # Hardware-accelerated video encoding
        video_codec = self._ffmpeg_config.get('video_codec', 'libx264')
        preset = self._ffmpeg_config.get('preset', cfg.video_preset)
        threads = self._ffmpeg_config.get('threads', 0)
        
        ffmpeg_cmd.extend([
            "-vf", ",".join(video_filters),
            "-c:v", video_codec,
        ])
        
        # Preset settings depend on codec
        if video_codec == "h264_nvenc":
            # NVIDIA NVENC settings
            ffmpeg_cmd.extend([
                "-preset", self._ffmpeg_config.get('preset_nvenc', 'p4'),
                "-rc", self._ffmpeg_config.get('rc', 'vbr'),
                "-gpu", self._ffmpeg_config.get('gpu', '0'),
            ])
            logger.info(f"Using NVIDIA NVENC encoder (preset {self._ffmpeg_config.get('preset_nvenc', 'p4')})")
        elif video_codec in ["h264_vaapi", "h264_videotoolbox"]:
            # AMD or Apple hardware encoding
            logger.info(f"Using {video_codec} hardware encoder")
        else:
            # Software encoding
            ffmpeg_cmd.extend([
                "-preset", preset,
                "-threads", str(threads) if threads > 0 else "0",
            ])
            logger.info(f"Using software encoder with {threads if threads > 0 else 'auto'} threads, preset {preset}")
        
        ffmpeg_cmd.extend([
            "-crf", str(cfg.video_crf),
            "-profile:v", cfg.video_profile,
            "-level:v", cfg.video_level,
            "-pix_fmt", "yuv420p",
        ])

        if cfg.video_maxrate:
            ffmpeg_cmd.extend(["-maxrate", cfg.video_maxrate])
        
        # Use optimized buffer size
        buffer_size = self._ffmpeg_config.get('buffer_size', cfg.video_bufsize or "4M")
        ffmpeg_cmd.extend(["-bufsize", buffer_size])

        ffmpeg_cmd.extend([
            "-c:a", "aac",
            "-ac", str(cfg.audio_channels),
            "-b:a", cfg.audio_bitrate,
            "-f", "hls",
            "-hls_time", str(cfg.hls_time),
            "-hls_list_size", str(cfg.hls_list_size),
            "-hls_flags", "delete_segments+append_list",
            "-hls_segment_filename", str(self._hls_dir / "segment%03d.ts"),
            str(self._hls_dir / "stream.m3u8"),
        ])
        
        logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")

        # For debugging, log FFmpeg output to a file
        ffmpeg_log = self._hls_dir / "ffmpeg.log"
        self._ffmpeg_log_handle = open(str(ffmpeg_log), "w")
        self._ffmpeg_log_path = ffmpeg_log
        
        try:
            self._ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=self._ffmpeg_log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self._ffmpeg_log_handle.close()
            self._ffmpeg_log_handle = None
            raise FFmpegCastingError(
                "FFmpeg not found. Please install FFmpeg to enable network casting."
            )
        except Exception as e:
            self._ffmpeg_log_handle.close()
            self._ffmpeg_log_handle = None
            raise FFmpegCastingError(f"Failed to start FFmpeg: {e}")

        # Wait for first segment to be created
        startup_deadline = time.monotonic() + max(5, cfg.startup_timeout)
        manifest_path = self._hls_dir / "stream.m3u8"

        while time.monotonic() < startup_deadline:
            if manifest_path.exists():
                break

            if self._ffmpeg_process and self._ffmpeg_process.poll() is not None:
                return_code = self._ffmpeg_process.returncode
                self._persist_failure_logs(
                    "ffmpeg_exit_during_startup",
                    video_path,
                    cfg,
                    {
                        "return_code": return_code,
                        "subtitle_on_cast": bool(self._active_subtitle_path),
                    },
                )
                self.stop()
                raise FFmpegCastingError(
                    f"FFmpeg exited prematurely while starting stream (return code {return_code})."
                )

            time.sleep(0.5)
        else:
            self._persist_failure_logs(
                "startup_timeout",
                video_path,
                cfg,
                {
                    "subtitle_on_cast": bool(self._active_subtitle_path),
                },
            )
            self.stop()
            raise FFmpegCastingError(
                f"Stream failed to initialize within {cfg.startup_timeout} seconds"
            )

        # Start HTTP server with proper HLS MIME types
        hls_server_script = PROJECT_ROOT / "src" / "hls_http_server.py"
        http_cmd = [
            "python3",
            str(hls_server_script),
            str(cfg.port),
            "-d", str(self._hls_dir),
        ]

        # For debugging, log HTTP server output to a file
        http_log = self._hls_dir / "http.log"
        self._http_log_handle = open(str(http_log), "w")
        self._http_log_path = http_log

        try:
            self._http_server_process = subprocess.Popen(
                http_cmd,
                stdout=self._http_log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
            )
        except Exception as e:
            self._persist_failure_logs(
                "http_server_start_failure",
                video_path,
                cfg,
                {
                    "error": str(e),
                },
            )
            self.stop()
            raise FFmpegCastingError(f"Failed to start HTTP server: {e}")

        # Give HTTP server a moment to start
        time.sleep(1)

        # Verify server is running
        if self._http_server_process.poll() is not None:
            self._persist_failure_logs(
                "http_server_exited",
                video_path,
                cfg,
                {
                    "return_code": self._http_server_process.returncode,
                },
            )
            self.stop()
            raise FFmpegCastingError("HTTP server failed to start")

        self._active_config = cfg
        self._active_video_path = video_path
        
        # Save PIDs for manual cleanup if needed
        pid_file = Path("/tmp/subtitle_player_stream.pids")
        try:
            pid_file.write_text(
                f"{self._ffmpeg_process.pid} {self._http_server_process.pid}\n"
            )
        except Exception:
            pass

        return self.url

    def stop(self) -> None:
        """Stop the active casting session."""
        if self._ffmpeg_process is not None:
            try:
                self._ffmpeg_process.terminate()
                self._ffmpeg_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._ffmpeg_process.kill()
            except Exception:
                pass
            self._ffmpeg_process = None

        if self._http_server_process is not None:
            try:
                self._http_server_process.terminate()
                self._http_server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._http_server_process.kill()
            except Exception:
                pass
            self._http_server_process = None

        if self._ffmpeg_log_handle is not None:
            try:
                self._ffmpeg_log_handle.close()
            except Exception:
                pass
            self._ffmpeg_log_handle = None
        self._ffmpeg_log_path = None

        if self._http_log_handle is not None:
            try:
                self._http_log_handle.close()
            except Exception:
                pass
            self._http_log_handle = None
        self._http_log_path = None

        if self._hls_dir and self._hls_dir.exists():
            try:
                for file in self._hls_dir.glob("*"):
                    file.unlink()
                self._hls_dir.rmdir()
            except Exception:
                pass

        pid_file = Path("/tmp/subtitle_player_stream.pids")
        if pid_file.exists():
            try:
                pid_file.unlink()
            except Exception:
                pass

        self._active_config = None
        self._active_video_path = None
        self._active_subtitle_path = None
        self._hls_dir = None

    def _flush_logs(self) -> None:
        for handle in (self._ffmpeg_log_handle, self._http_log_handle):
            if handle:
                try:
                    handle.flush()
                except Exception:
                    pass

    def _persist_failure_logs(
        self,
        reason: str,
        video_path: str,
        config: FFmpegCastingConfig,
        extra: Optional[Dict[str, object]] = None,
    ) -> Optional[Path]:
        """Copy FFmpeg/HTTP logs to the project logs directory for post-mortem analysis."""

        try:
            self._flush_logs()

            archive_root = LOG_ARCHIVE_DIR
            archive_root.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safe_name = Path(video_path).stem or "video"
            safe_name = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in safe_name
            )
            bundle_dir = archive_root / f"{timestamp}_{safe_name[:48]}"

            counter = 1
            while bundle_dir.exists():
                counter += 1
                bundle_dir = archive_root / f"{timestamp}_{safe_name[:48]}_{counter}"

            bundle_dir.mkdir(parents=True, exist_ok=False)

            metadata: Dict[str, object] = {
                "reason": reason,
                "video_path": video_path,
                "subtitle_path": self._active_subtitle_path,
                "config": {
                    "host": config.host,
                    "port": config.port,
                    "hls_time": config.hls_time,
                    "hls_list_size": config.hls_list_size,
                    "startup_timeout": config.startup_timeout,
                    "target_height": config.target_height,
                    "video_crf": config.video_crf,
                    "video_preset": config.video_preset,
                    "video_profile": config.video_profile,
                    "video_level": config.video_level,
                    "video_maxrate": config.video_maxrate,
                    "video_bufsize": config.video_bufsize,
                    "audio_bitrate": config.audio_bitrate,
                    "audio_channels": config.audio_channels,
                },
                "ffmpeg_return_code": self._ffmpeg_process.returncode if self._ffmpeg_process else None,
                "http_return_code": self._http_server_process.returncode if self._http_server_process else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            if extra:
                metadata.update(extra)

            (bundle_dir / "metadata.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            if self._ffmpeg_log_path and self._ffmpeg_log_path.exists():
                shutil.copy(self._ffmpeg_log_path, bundle_dir / "ffmpeg.log")

            if self._http_log_path and self._http_log_path.exists():
                shutil.copy(self._http_log_path, bundle_dir / "http.log")

            return bundle_dir
        except Exception:
            return None

    @staticmethod
    def _build_subtitle_filter(subtitle_path: str) -> str:
        """Escape and build the FFmpeg subtitles filter argument."""
        resolved = Path(subtitle_path).resolve()
        escaped = str(resolved).replace("\\", "\\\\")
        escaped = escaped.replace(":", "\\:")
        escaped = escaped.replace(",", "\\,")
        escaped = escaped.replace("'", "\\'")
        escaped = escaped.replace("[", "\\[").replace("]", "\\]")
        escaped = escaped.replace("(", "\\(").replace(")", "\\)")
        escaped = escaped.replace(" ", "\\ ")
        return f"subtitles={escaped}"

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.stop()

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.cleanup()
