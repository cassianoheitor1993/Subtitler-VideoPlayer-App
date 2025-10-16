"""Casting manager for VLC-based streaming outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import vlc


@dataclass
class CastingConfig:
    """Configuration for a casting session."""

    host: str = "0.0.0.0"
    port: int = 8080
    transcode: bool = False
    video_codec: str = "h264"
    audio_codec: str = "mp4a"
    mux: str = "ts"
    ttl: Optional[int] = None


class CastingError(RuntimeError):
    """Raised when casting actions fail."""


class CastingManager:
    """Manage VLC stream output sessions."""

    def __init__(self, instance: vlc.Instance) -> None:
        self._instance = instance
        self._stream_player: Optional[vlc.MediaPlayer] = None
        self._active_config: Optional[CastingConfig] = None
        self._active_url: Optional[str] = None

    @property
    def is_casting(self) -> bool:
        return self._stream_player is not None

    @property
    def url(self) -> Optional[str]:
        return self._active_url

    def start_http_stream(
        self,
        media: vlc.Media,
        config: Optional[CastingConfig] = None,
        *,
        loop: bool = False,
    ) -> str:
        if self.is_casting:
            raise CastingError("Casting session already active")

        cfg = config or CastingConfig()
        stream_media = None
        if hasattr(media, "duplicate"):
            stream_media = media.duplicate()
        if stream_media is None:
            mrl = media.get_mrl() if hasattr(media, "get_mrl") else None
            if not mrl:
                raise CastingError("Unable to prepare media for casting")
            stream_media = self._instance.media_new(mrl)

        if loop:
            stream_media.add_option(":input-repeat=-1")

        sout_parts = []
        
        if cfg.transcode:
            transcode_segment = (
                f"transcode{{vcodec={cfg.video_codec},acodec={cfg.audio_codec}}}"
            )
            sout_parts.append(transcode_segment)

        mux = cfg.mux
        access = "http"
        dst = f"{cfg.host}:{cfg.port}"
        
        std_segment = f"std{{access={access},mux={mux},dst={dst}}}"
        sout_parts.append(std_segment)

        sout_chain = ":".join(sout_parts)
        stream_media.add_option(f":sout={sout_chain}")
        stream_media.add_option(":sout-keep")
        stream_media.add_option(":sout-all")
        stream_media.add_option(":network-caching=1000")
        if cfg.ttl is not None:
            stream_media.add_option(f":ttl={cfg.ttl}")

        player = self._instance.media_player_new()
        player.set_media(stream_media)

        if player.play() != 0:
            raise CastingError("Failed to start casting stream")

        self._stream_player = player
        self._active_config = cfg
        self._active_url = f"http://{cfg.host}:{cfg.port}/"
        return self._active_url

    def stop(self) -> None:
        if self._stream_player is None:
            return

        self._stream_player.stop()
        self._stream_player.release()
        self._stream_player = None
        self._active_config = None
        self._active_url = None

    def cleanup(self) -> None:
        self.stop()